# -*- coding: utf-8 -*-
"""Lettre de motivation : le LLM ne rédige que les deux parties propres à l'offre.

La motivation personnelle et le parcours restent des `[À REMPLIR PAR MARCEL]`.
Le vocabulaire technique des parties rédigées est limité à la `Selection` et à
l'offre elle-même.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from pathlib import Path

from cvgen.catalog import projet_index, resolve
from cvgen.models import Catalog, LetterDraft, OfferAnalysis, Selection, numbers, tech_tokens

from .llm import LLMProvider

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SKELETON_PATH = ROOT / "data" / "lm_skeleton.md"

PLACEHOLDER_RE = re.compile(r"\[À REMPLIR PAR MARCEL[^\]]*\]")
VILLE_EXPEDITION = "Clermont-Ferrand"

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"]

SYSTEM = """Tu rédiges deux paragraphes d'une lettre de motivation en français.

Contraintes absolues :
- Tu ne peux citer QUE les projets et compétences listés dans la sélection fournie, et
  les éléments de l'offre. Aucune autre technologie, aucun autre projet, aucun chiffre
  qui ne vienne pas de ces deux sources.
- N'invente jamais la motivation personnelle du candidat, ses goûts, ses valeurs, ni un
  lien affectif avec l'entreprise. D'autres paragraphes, écrits par lui, s'en chargent.
- Ton sobre et factuel. Pas de superlatif, pas de formule creuse ("depuis toujours
  passionné", "votre entreprise leader", "c'est avec un grand enthousiasme").
- Pas de flatterie. Pas de conditionnel de politesse à rallonge.
- Français, vouvoiement, environ 130 mots par paragraphe."""

PROMPT = """# Offre

Poste : {poste}
Entreprise : {entreprise}
Lieu : {lieu}
Contrat : {contrat}

Missions :
{missions}

Compétences requises : {requises}
Compétences appréciées : {appreciees}

# Sélection retenue pour le CV (seule matière autorisée)

Intitulé ciblé : {role}

Projets :
{projets}

Compétences :
{competences}

# Ce que tu dois produire

- `pourquoi_entreprise` : ce que fait l'entreprise et en quoi le poste décrit dans
  l'offre correspond à ce que le candidat cherche à faire. Appuie-toi sur des éléments
  concrets de l'offre (le périmètre du poste, les missions, le secteur). N'attribue
  aucun sentiment au candidat.
- `adequation_missions` : la mise en regard des missions de l'offre avec les projets de
  la sélection ci-dessus. Nomme les projets et les compétences tels qu'ils sont écrits.
  Reste vérifiable : ce paragraphe doit être défendable en entretien.
{correction}"""

RETRY_HEADER = """
# CORRECTION REQUISE

Ta réponse précédente a été rejetée :

{erreur}

Réécris les deux paragraphes sans ces éléments.
"""


class LetterError(Exception):
    """Brouillon de lettre non conforme, ou squelette non relu."""


def _format_date(jour: dt.date) -> str:
    return f"{jour.day} {MOIS_FR[jour.month - 1]} {jour.year}"


def _allowed_tokens(
    selection: Selection, catalog: Catalog, analysis: OfferAnalysis
) -> tuple[set[str], set[str]]:
    """Technos et chiffres citables : ceux de la sélection et ceux de l'offre."""
    cv = resolve(selection, catalog)
    competences = {c.id: c for c in catalog.competences}

    textes = [cv.tagline, selection.role, catalog.contact.nom, VILLE_EXPEDITION]
    for projet in cv.projets:
        textes += [projet.titre, *projet.bullets]
    for groupe in selection.skill_groups:
        textes.append(catalog.categories[groupe.categorie])
        textes += [competences[i].label for i in groupe.skill_ids]
    # L'offre est une source légitime : nom de l'entreprise, outils qu'elle cite, lieu.
    textes += [analysis.intitule, analysis.entreprise, analysis.lieu, analysis.type_contrat]
    textes += analysis.missions + analysis.competences_requises
    textes += analysis.competences_appreciees + analysis.mots_cles

    technos: set[str] = set()
    chiffres: set[str] = set()
    for texte in textes:
        technos |= tech_tokens(texte, any_position=True)
        chiffres |= numbers(texte)
    return technos, chiffres


def check_draft(
    draft: LetterDraft, selection: Selection, catalog: Catalog, analysis: OfferAnalysis
) -> list[str]:
    technos, chiffres = _allowed_tokens(selection, catalog, analysis)
    violations: list[str] = []

    for champ, texte in (("pourquoi_entreprise", draft.pourquoi_entreprise),
                         ("adequation_missions", draft.adequation_missions)):
        inconnues = sorted(tech_tokens(texte) - technos)
        if inconnues:
            violations.append(f"{champ} : termes hors sélection et hors offre : {inconnues}")
        nouveaux = sorted(numbers(texte) - chiffres)
        if nouveaux:
            violations.append(f"{champ} : chiffres inédits : {nouveaux}")

    return violations


def build_draft(
    analysis: OfferAnalysis,
    selection: Selection,
    catalog: Catalog,
    provider: LLMProvider,
) -> LetterDraft:
    """Un seul retry, avec les violations renvoyées au LLM. Puis échec."""
    cv = resolve(selection, catalog)
    competences = {c.id: c for c in catalog.competences}
    projets = projet_index(catalog)

    bloc_projets = "\n".join(
        f"- {p.titre} ({projets[p.id].dates})\n" + "\n".join(f"    {b}" for b in p.bullets)
        for p in cv.projets
    )
    bloc_competences = "\n".join(
        f"- {catalog.categories[g.categorie]} : "
        + ", ".join(competences[i].label for i in g.skill_ids)
        for g in selection.skill_groups
    )

    base = {
        "poste": analysis.intitule or "(non précisé)",
        "entreprise": analysis.entreprise or "(non précisée)",
        "lieu": analysis.lieu or "(non précisé)",
        "contrat": analysis.type_contrat or "(non précisé)",
        "missions": "\n".join(f"- {m}" for m in analysis.missions) or "- (non précisées)",
        "requises": ", ".join(analysis.competences_requises) or "(non précisées)",
        "appreciees": ", ".join(analysis.competences_appreciees) or "(non précisées)",
        "role": selection.role,
        "projets": bloc_projets,
        "competences": bloc_competences,
    }

    erreur: str | None = None
    for tentative in (1, 2):
        prompt = PROMPT.format(
            **base, correction=RETRY_HEADER.format(erreur=erreur) if erreur else ""
        )
        draft = provider.structured(prompt, LetterDraft, system=SYSTEM)
        violations = check_draft(draft, selection, catalog, analysis)
        if not violations:
            return draft
        erreur = " ; ".join(violations)
        if tentative == 1:
            LOGGER.warning("Brouillon de LM rejeté, nouvelle tentative : %s", erreur)
    raise LetterError(f"Brouillon de LM toujours non conforme après un retry : {erreur}")


def fill_skeleton(
    draft: LetterDraft,
    analysis: OfferAnalysis,
    catalog: Catalog,
    aujourdhui: dt.date | None = None,
    skeleton_path: Path | None = None,
) -> str:
    """Remplit le squelette. Les [À REMPLIR PAR MARCEL] restent tels quels."""
    texte = (skeleton_path or SKELETON_PATH).read_text(encoding="utf-8")
    texte = re.sub(r"<!--.*?-->\n?", "", texte, flags=re.DOTALL)

    valeurs = {
        "contact_nom": catalog.contact.nom,
        "contact_adresse": catalog.contact.adresse,
        "contact_email": catalog.contact.email,
        "contact_tel": catalog.contact.tel,
        "entreprise": analysis.entreprise or "",
        "lieu": analysis.lieu or "",
        "ville_expedition": VILLE_EXPEDITION,
        "date": _format_date(aujourdhui or dt.date.today()),
        "poste": analysis.intitule or "",
        "pourquoi_entreprise": draft.pourquoi_entreprise,
        "adequation_missions": draft.adequation_missions,
        "disponibilite_duree": catalog.disponibilite.duree,
        "disponibilite_debut": catalog.disponibilite.debut,
    }
    for cle, valeur in valeurs.items():
        texte = texte.replace("{{ " + cle + " }}", valeur)

    restants = re.findall(r"\{\{\s*(\w+)\s*\}\}", texte)
    if restants:
        raise LetterError(f"Placeholders non résolus dans le squelette : {sorted(set(restants))}")

    return texte.strip() + "\n"


def remaining_placeholders(markdown: str) -> list[str]:
    return PLACEHOLDER_RE.findall(markdown)
