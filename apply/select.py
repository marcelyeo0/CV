# -*- coding: utf-8 -*-
"""Sélection des projets et compétences pertinents : `OfferAnalysis` -> `Selection`.

Le LLM ne reçoit que des identifiants et ne peut renvoyer que des identifiants.
Toute sortie passe par `validate_selection` ; en cas d'échec, l'erreur lui est
renvoyée une seule fois, puis l'échec est définitif.
"""

from __future__ import annotations

import json
import logging

from cvgen.catalog import SelectionError, validate_selection
from cvgen.models import Catalog, OfferAnalysis, Selection, SelectionDraft

from .llm import LLMProvider

LOGGER = logging.getLogger(__name__)

MAX_PROJECTS = 3

SYSTEM = """Tu sélectionnes, dans le catalogue d'un candidat, les éléments les plus
pertinents pour une offre d'emploi. Tu n'es pas rédacteur : tu choisis et tu ordonnes.

Interdictions absolues :
- N'invente aucun projet, compétence, technologie, chiffre ou expérience.
- N'utilise que les identifiants exacts fournis dans le catalogue.
- Ne mets aucune date ni durée de disponibilité dans le champ `role` : elles viennent
  du catalogue, pas de toi.
- Si une compétence demandée par l'offre n'est pas dans le catalogue, ne la fabrique pas :
  mets-la dans `missing_keywords`."""

PROMPT = """# Offre analysée

{analyse}

# Catalogue du candidat

## Catégories de compétences autorisées
{categories}

## Compétences (id — libellé — catégories autorisées)
{competences}

## Projets (id — titre — dates — tags, puis puces numérotées)
{projets}

# Ce que tu dois produire

- `role` : l'intitulé ciblé, calé sur celui de l'offre, sans date ni durée.
  Exemples de forme attendue : "Data Analyst", "Market Intelligence & Insights".
- `projects` : au maximum {max_projects} projets, du plus au moins pertinent.
  Pour chacun, `bullet_indices` liste les puces à afficher, dans l'ordre (2 à 3 puces
  par projet). Les indices renvoient à la numérotation ci-dessus.
- `skill_groups` : les groupes de compétences, dans l'ordre d'affichage souhaité.
  `categorie` est une clé de la liste des catégories autorisées, `skill_ids` des ids de
  compétences. Place en tête les catégories et les compétences que l'offre demande.
  Une compétence ne peut aller que dans une catégorie qui lui est autorisée. Deux
  formulations de la même chose (par exemple `sql` et `sql_postgresql`) ne peuvent pas
  cohabiter dans un même groupe.
- `bullet_overrides` : facultatif. Reformulation d'une puce pour mieux coller au
  vocabulaire de l'offre. Tu ne peux que réécrire : aucune technologie ni aucun chiffre
  qui ne figure pas déjà dans le catalogue. En cas de doute, ne reformule pas.
- `justification` : 2 phrases maximum expliquant ce choix.
- `missing_keywords` : les mots-clés de l'offre qui n'ont aucun équivalent dans le
  catalogue. C'est au candidat de décider s'il les ajoute ; ne les invente jamais.
{correction}"""

RETRY_HEADER = """
# CORRECTION REQUISE

Ta réponse précédente a été rejetée par la validation :

{erreur}

Reprends en corrigeant uniquement ce point. N'utilise que des identifiants du catalogue
ci-dessus.
"""


def _digest_categories(catalog: Catalog) -> str:
    return "\n".join(f"- {cle} : {libelle}" for cle, libelle in catalog.categories.items())


def _digest_competences(catalog: Catalog) -> str:
    return "\n".join(
        f"- {c.id} — {c.label} — {', '.join(c.categories)}" for c in catalog.competences
    )


def _digest_projets(catalog: Catalog) -> str:
    blocs = []
    for projet in catalog.projets:
        lignes = [f"- {projet.id} — {projet.titre} — {projet.dates} — tags: {', '.join(projet.tags)}"]
        lignes += [f"    [{i}] {b}" for i, b in enumerate(projet.bullets)]
        blocs.append("\n".join(lignes))
    return "\n".join(blocs)


def _digest_analyse(analysis: OfferAnalysis) -> str:
    return json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2)


def build_prompt(analysis: OfferAnalysis, catalog: Catalog, erreur: str | None = None) -> str:
    return PROMPT.format(
        analyse=_digest_analyse(analysis),
        categories=_digest_categories(catalog),
        competences=_digest_competences(catalog),
        projets=_digest_projets(catalog),
        max_projects=MAX_PROJECTS,
        correction=RETRY_HEADER.format(erreur=erreur) if erreur else "",
    )


def build_selection(
    analysis: OfferAnalysis,
    catalog: Catalog,
    provider: LLMProvider,
) -> Selection:
    """Un seul retry, avec l'erreur de validation renvoyée au LLM. Puis échec."""
    erreur: str | None = None

    for tentative in (1, 2):
        draft = provider.structured(
            build_prompt(analysis, catalog, erreur), SelectionDraft, system=SYSTEM
        )
        selection = draft.to_selection()
        try:
            # strict : une reformulation fautive doit remonter au LLM, pas être
            # silencieusement ignorée.
            selection = validate_selection(selection, catalog, strict=True)
        except SelectionError as exc:
            erreur = str(exc)
            if tentative == 1:
                LOGGER.warning("Sélection rejetée, nouvelle tentative : %s", erreur)
                continue
            raise SelectionError(
                f"Sélection toujours invalide après un retry : {erreur}"
            ) from exc

        LOGGER.info(
            "Sélection retenue : role=%s projets=%s mots-clés manquants=%s",
            selection.role, selection.project_ids, selection.missing_keywords,
        )
        return selection

    raise AssertionError("inatteignable")
