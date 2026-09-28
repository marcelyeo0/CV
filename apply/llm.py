# -*- coding: utf-8 -*-
"""Accès LLM isolé derrière une interface minimale.

Tout le reste du code ne connaît que `LLMProvider.structured(...)`. Changer de
fournisseur revient à écrire une autre classe respectant ce protocole.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Protocol, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "gemini-3.8-flash"
# Déterminisme : on veut une sélection reproductible, pas de la créativité.
DEFAULT_TEMPERATURE = 0.2

# Erreurs côté serveur, sans rapport avec la requête : saturation, quota court terme.
TRANSIENT_CODES = ("503", "429", "500", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
TRANSIENT_ATTEMPTS = 4
TRANSIENT_BACKOFF_S = 4.0

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Appel LLM impossible ou réponse inexploitable."""

# Sous-ensemble de JSON Schema accepté par l'API Gemini. Tout le reste doit être
# retiré : `additionalProperties`, que Pydantic émet à cause de extra="forbid",
# provoque un 400 INVALID_ARGUMENT.
_GEMINI_SCHEMA_KEYS = frozenset({
    "type", "format", "description", "nullable", "enum", "items",
    "properties", "required", "propertyOrdering", "minItems", "maxItems",
})


def gemini_schema(model: type[BaseModel]) -> dict:
    """JSON Schema d'un modèle Pydantic, ramené à ce que Gemini accepte.

    Les `$ref` sont résolus sur place : l'API ne gère pas les définitions
    partagées.
    """
    raw = model.model_json_schema()
    definitions = raw.pop("$defs", {})

    def resolve(node, profondeur: int = 0):
        if profondeur > 20:
            raise LLMError(f"Schéma {model.__name__} trop imbriqué ou récursif")
        if isinstance(node, list):
            return [resolve(item, profondeur + 1) for item in node]
        if not isinstance(node, dict):
            return node

        ref = node.get("$ref")
        if ref:
            nom = ref.rsplit("/", 1)[-1]
            if nom not in definitions:
                raise LLMError(f"Définition introuvable dans le schéma : {ref}")
            fusion = {**definitions[nom], **{k: v for k, v in node.items() if k != "$ref"}}
            return resolve(fusion, profondeur + 1)

        propre = {}
        for cle, valeur in node.items():
            if cle not in _GEMINI_SCHEMA_KEYS:
                continue
            if cle == "properties":
                propre[cle] = {k: resolve(v, profondeur + 1) for k, v in valeur.items()}
            elif cle in ("items",):
                propre[cle] = resolve(valeur, profondeur + 1)
            else:
                propre[cle] = valeur
        return propre

    return resolve(raw)


class LLMProvider(Protocol):
    """Renvoie une instance de `schema` remplie par le modèle."""

    def structured(self, prompt: str, schema: type[T], system: str = "") -> T:
        ...


class GeminiProvider:
    """Sortie structurée Gemini : `response_schema` + validation Pydantic."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        load_dotenv(ROOT / ".env")

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            raise LLMError(
                "GEMINI_API_KEY absente. Copier .env.example vers .env et y mettre la clé "
                "(https://aistudio.google.com/apikey)."
            )

        self.model = model or os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
        if temperature is not None:
            self.temperature = temperature
        else:
            raw = os.environ.get("GEMINI_TEMPERATURE", "").strip()
            self.temperature = float(raw) if raw else DEFAULT_TEMPERATURE

        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai  # import tardif : aucun réseau tant qu'on n'appelle pas

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _call_with_backoff(self, prompt: str, config, nom_schema: str):
        """Reprend sur les erreurs transitoires de l'API (503, 429, 500)."""
        import time

        derniere: Exception | None = None
        for tentative in range(1, TRANSIENT_ATTEMPTS + 1):
            try:
                return self._get_client().models.generate_content(
                    model=self.model, contents=prompt, config=config
                )
            except Exception as exc:  # l'API remonte des erreurs hétérogènes
                derniere = exc
                message = str(exc)
                transitoire = any(code in message for code in TRANSIENT_CODES)
                if not transitoire or tentative == TRANSIENT_ATTEMPTS:
                    break
                attente = TRANSIENT_BACKOFF_S * (2 ** (tentative - 1))
                LOGGER.warning(
                    "Erreur transitoire sur %s (tentative %d/%d), reprise dans %.0f s : %s",
                    nom_schema, tentative, TRANSIENT_ATTEMPTS, attente, message.split("\n")[0],
                )
                time.sleep(attente)

        raise LLMError(f"Appel Gemini ({self.model}) échoué : {derniere}") from derniere

    def structured(self, prompt: str, schema: type[T], system: str = "") -> T:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=gemini_schema(schema),
            temperature=self.temperature,
            system_instruction=system or None,
            # Le schéma est passé en dict : le SDK ne peut plus désérialiser seul,
            # donc aucune fonction n'est appelée automatiquement.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        LOGGER.info("Appel %s -> %s", self.model, schema.__name__)
        response = self._call_with_backoff(prompt, config, schema.__name__)

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, schema):
            return parsed

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise LLMError(f"Réponse vide du modèle pour {schema.__name__}")
        try:
            return schema.model_validate_json(text)
        except ValidationError as exc:
            raise LLMError(
                f"Réponse non conforme à {schema.__name__} : {exc}\nReçu : {text[:500]}"
            ) from exc
