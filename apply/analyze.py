# -*- coding: utf-8 -*-
"""Analyse d'une offre d'emploi : texte brut -> `OfferAnalysis` structurée."""

from __future__ import annotations

import logging

from cvgen.models import OfferAnalysis

from .llm import LLMProvider

LOGGER = logging.getLogger(__name__)

# Au-delà, on tronque : les offres longues répètent surtout des mentions légales.
MAX_CHARS = 20000

SYSTEM = """Tu extrais des informations d'une offre d'emploi. Tu es un extracteur, pas un rédacteur.

Règles absolues :
- N'extrais que ce qui est écrit dans l'offre. N'invente rien, ne déduis rien.
- Un champ dont l'information est absente de l'offre reste vide (chaîne vide ou liste vide).
- Conserve les termes techniques tels qu'ils sont écrits dans l'offre (casse et orthographe
  d'origine : « PostgreSQL », « scikit-learn », « Power BI »).
- Ne traduis pas : garde la langue de l'offre."""

PROMPT = """Analyse l'offre d'emploi ci-dessous et remplis la structure demandée.

- intitule : le titre du poste tel qu'écrit dans l'offre.
- entreprise : le nom de l'entreprise qui recrute (vide si l'offre est anonyme).
- lieu : ville ou zone géographique du poste.
- type_contrat : stage, alternance, CDI, CDD, freelance... tel qu'indiqué.
- competences_requises : compétences, technologies et savoir-faire présentés comme
  obligatoires ou attendus.
- competences_appreciees : celles présentées comme un plus, un atout, optionnelles.
- mots_cles : les termes techniques et métier saillants de l'offre, un par entrée,
  sans phrase. Ce sont eux qui serviront à mesurer la couverture d'un profil.
- missions : les missions confiées, une par entrée, formulées comme dans l'offre.
- langue : "fr" si l'offre est rédigée en français, "en" en anglais, sinon "autre".

OFFRE :
---
{offre}
---"""


def analyze_offer(text: str, provider: LLMProvider) -> OfferAnalysis:
    if not text.strip():
        raise ValueError("Texte d'offre vide")

    if len(text) > MAX_CHARS:
        LOGGER.warning("Offre tronquée à %d caractères (longueur %d)", MAX_CHARS, len(text))
        text = text[:MAX_CHARS]

    analysis = provider.structured(PROMPT.format(offre=text), OfferAnalysis, system=SYSTEM)
    LOGGER.info(
        "Offre analysée : %s / %s (%s) — %d mots-clés",
        analysis.intitule or "intitulé inconnu",
        analysis.entreprise or "entreprise inconnue",
        analysis.langue,
        len(analysis.mots_cles),
    )
    return analysis
