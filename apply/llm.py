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

DEFAULT_MODEL = "gemini-2.5-flash"
# Déterminisme : on veut une sélection reproductible, pas de la créativité.
DEFAULT_TEMPERATURE = 0.2

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Appel LLM impossible ou réponse inexploitable."""


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

    def structured(self, prompt: str, schema: type[T], system: str = "") -> T:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=self.temperature,
            system_instruction=system or None,
        )

        LOGGER.info("Appel %s -> %s", self.model, schema.__name__)
        try:
            response = self._get_client().models.generate_content(
                model=self.model, contents=prompt, config=config
            )
        except Exception as exc:  # l'API remonte des erreurs hétérogènes
            raise LLMError(f"Appel Gemini ({self.model}) échoué : {exc}") from exc

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
