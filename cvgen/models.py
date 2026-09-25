# -*- coding: utf-8 -*-
"""Schémas Pydantic du catalogue, de la sélection et de l'analyse d'offre.

Règle structurante : une `Selection` ne contient que des identifiants du
catalogue (plus, éventuellement, des reformulations de puces soumises à une
liste blanche). Aucun contenu factuel nouveau ne peut y entrer.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

class Contact(_Base):
    nom: str
    email: str
    tel: str
    adresse: str
    adresse_courte: str
    github_url: str


class Disponibilite(_Base):
    duree: str
    debut: str
    gabarit_tagline: str

    def tagline(self, role: str) -> str:
        return self.gabarit_tagline.format(duree=self.duree, role=role, debut=self.debut)


class Formation(_Base):
    titre: str
    dates: str
    etab: str


class Experience(_Base):
    id: str
    titre: str
    dates: str
    etab: str
    bullets: list[str]


class Projet(_Base):
    id: str
    titre: str
    dates: str
    tags: list[str] = Field(default_factory=list)
    bullets: list[str]
    bullets_defaut: list[int] | None = None

    def indices_defaut(self) -> list[int]:
        if self.bullets_defaut is None:
            return list(range(len(self.bullets)))
        return list(self.bullets_defaut)


class Competence(_Base):
    id: str
    label: str
    groupe: str
    categories: list[str]
    tags: list[str] = Field(default_factory=list)


class SkillGroup(_Base):
    categorie: str
    skill_ids: list[str]


class BulletOverride(_Base):
    """Reformulation d'une puce. `index` indexe `Projet.bullets`."""
    projet_id: str
    index: int
    texte: str


class Selection(_Base):
    role: str                                   # intitulé ciblé, sans disponibilité
    project_ids: list[str]
    skill_groups: list[SkillGroup]
    bullet_selection: dict[str, list[int]] = Field(default_factory=dict)
    bullet_overrides: list[BulletOverride] = Field(default_factory=list)
    justification: str = ""
    missing_keywords: list[str] = Field(default_factory=list)


class Catalog(_Base):
    contact: Contact
    disponibilite: Disponibilite
    formation: list[Formation]
    experiences: list[Experience]
    projet_academique: list[Projet]
    projets: list[Projet]
    categories: dict[str, str]
    competences: list[Competence]
    langues: list[str]
    centres_interet: list[str]
    selections_par_defaut: dict[str, Selection]


# ---------------------------------------------------------------------------
# Analyse d'offre et lettre
# ---------------------------------------------------------------------------

class OfferAnalysis(_Base):
    intitule: str = ""
    entreprise: str = ""
    lieu: str = ""
    type_contrat: str = ""
    competences_requises: list[str] = Field(default_factory=list)
    competences_appreciees: list[str] = Field(default_factory=list)
    mots_cles: list[str] = Field(default_factory=list)
    missions: list[str] = Field(default_factory=list)
    langue: Literal["fr", "en", "autre"] = "fr"


class LetterDraft(_Base):
    """Seules les deux sections spécifiques à l'offre sont rédigées par le LLM."""
    pourquoi_entreprise: str
    adequation_missions: str


# ---------------------------------------------------------------------------
# Normalisation et détection de tokens « techno-formés »
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÿ][0-9A-Za-zÀ-ÿ._+#/-]*")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?\s*%?")


def normalize(token: str) -> str:
    """casefold + suppression des accents et de la ponctuation de bord."""
    token = token.strip(" .,;:()[]{}«»\"'…")
    decomposed = unicodedata.normalize("NFKD", token)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def is_tech_shaped(token: str, position: int) -> bool:
    """Heuristique : le token ressemble-t-il à un nom de techno / outil ?

    `position` est l'index du token dans la phrase (0 = début de phrase, où une
    majuscule ne signifie rien).
    """
    core = token.strip(".,;:")
    if not core:
        return False
    if any(ch in core for ch in "+#_"):
        return True
    if "." in core or "/" in core:
        return True
    if any(ch.isdigit() for ch in core) and any(ch.isalpha() for ch in core):
        return True
    if any(ch.isupper() for ch in core[1:]):          # majuscule interne : NumPy, PostgreSQL
        return True
    if core.isupper() and len(core) > 1:              # acronyme : RAG, ETL, ACP
        return True
    if position > 0 and core[0].isupper():            # majuscule hors début de phrase
        return True
    return False


def tech_tokens(text: str) -> set[str]:
    """Tokens techno-formés d'un texte, normalisés."""
    found: set[str] = set()
    for sentence in re.split(r"(?<=[.!?:;])\s+", text):
        for position, token in enumerate(tokenize(sentence)):
            if is_tech_shaped(token, position):
                normalized = normalize(token)
                if normalized:
                    found.add(normalized)
    return found


def numbers(text: str) -> set[str]:
    return {match.group(0).replace(" ", "") for match in _NUMBER_RE.finditer(text)}
