# -*- coding: utf-8 -*-
"""Lettre de motivation : les quatre paragraphes du corps sont rédigés par le LLM.

Les deux premiers se déduisent de l'offre et de la `Selection`. Les deux derniers
touchent au parcours et à la motivation : ils ne peuvent citer que des faits du
catalogue, mais restent des PROPOSITIONS à relire — c'est le seul endroit de la
chaîne où le texte n'est pas déductible d'une donnée vérifiable.
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

# Paragraphes dont la formulation ne se déduit pas d'une donnée : à relire.
CHAMPS_A_RELIRE = ("motivation_personnelle", "apport_parcours")

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"]

SYSTEM = """Tu rédiges les quatre paragraphes du corps d'une lettre de motivation en français.

Interdictions absolues :
- Aucun fait qui ne soit pas dans l'offre, dans la sélection ou dans le parcours fournis.
  Pas de technologie, pas de chiffre, pas de projet, pas d'employeur, pas de diplôme, pas
  d'anecdote qui ne vienne de ces sources.
- Pas d'affirmation invérifiable sur le candidat : pas de « depuis l'enfance », pas de
  passion déclarée pour une marque ou un produit, pas de valeur personnelle inventée, pas
  de rencontre ou de lecture imaginaire.
- Pas de superlatif, pas de flatterie, pas de formule creuse (« entreprise leader »,
  « c'est avec un grand enthousiasme », « votre prestigieuse société »).

Style : sobre, factuel, phrases courtes, vouvoiement, environ 110 mots par paragraphe.
Une lettre qui reste sous 400 mots au total tient sur une page."""

PROMPT = """# Offre

Poste : {poste}
Entreprise : {entreprise}
Lieu : {lieu}
Contrat : {contrat}

Missions :
{missions}

Compétences requises : {requises}
Compétences appréciées : {appreciees}

# Sélection retenue pour le CV

Intitulé ciblé : {role}

Projets :
{projets}

Compétences :
{competences}

# Parcours du candidat (seuls faits utilisables pour les paragraphes 3 et 4)

Formation :
{formation}

Expériences :
{experiences}

Projet académique :
{academique}

Langues : {langues}
Centres d'intérêt : {interets}

# Ce que tu dois produire

1. `pourquoi_entreprise` : ce que fait l'entreprise et le périmètre du poste, d'après
   l'offre. En quoi ce périmètre correspond au type de travail que le candidat cherche.
   N'attribue aucun sentiment au candidat.
2. `adequation_missions` : les missions de l'offre mises en regard des projets de la
   sélection. Nomme les projets et les compétences tels qu'ils sont écrits. Chaque
   affirmation doit être défendable en entretien.
3. `motivation_personnelle` : ce qui, dans ce métier et ces missions, justifie une
   candidature. Appuie-toi UNIQUEMENT sur des éléments du parcours ci-dessus : la nature
   des projets déjà menés, la formation suivie, les expériences, éventuellement un centre
   d'intérêt s'il éclaire vraiment le poste. Ne prétends pas connaître les goûts ou
   l'histoire du candidat au-delà de ces faits.
4. `apport_parcours` : ce que la formation et les expériences listées apportent pour ce
   poste précis. Reste sur des faits vérifiables et leur conséquence concrète.
{correction}"""

RETRY_HEADER = """
# CORRECTION REQUISE

Ta réponse précédente a été rejetée :

{erreur}

Réécris les quatre paragraphes sans ces éléments.
"""


class LetterError(Exception):
    """Brouillon de lettre non conforme."""


def _format_date(jour: dt.date) -> str:
    return f"{jour.day} {MOIS_FR[jour.month - 1]} {jour.year}"


def _allowed_tokens(
    selection: Selection, catalog: Catalog, analysis: OfferAnalysis
) -> tuple[set[str], set[str]]:
    """Technos, noms propres et chiffres citables.

    Trois sources légitimes : la sélection, le parcours du catalogue (qui figure de
    toute façon sur le CV), et l'offre elle-même.
    """
    cv = resolve(selection, catalog)
    competences = {c.id: c for c in catalog.competences}

    textes = [cv.tagline, selection.role, catalog.contact.nom, VILLE_EXPEDITION,
              catalog.disponibilite.duree, catalog.disponibilite.debut]

    for projet in cv.projets:
        textes += [projet.titre, *projet.bullets]
    for groupe in selection.skill_groups:
        textes.append(catalog.categories[groupe.categorie])
        textes += [competences[i].label for i in groupe.skill_ids]

    # Parcours : imprimé sur tous les CV, donc citable dans la lettre.
    for formation in catalog.formation:
        textes += [formation.titre, formation.dates, formation.etab]
    for experience in catalog.experiences:
        textes += [experience.titre, experience.dates, experience.etab, *experience.bullets]
    for projet in catalog.projet_academique:
        textes += [projet.titre, projet.dates, *projet.bullets]
    textes += catalog.langues + catalog.centres_interet

    # L'offre : nom de l'entreprise, lieu, outils et termes métier qu'elle cite.
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

    for champ in LetterDraft.model_fields:
        texte = getattr(draft, champ)
        inconnues = sorted(tech_tokens(texte) - technos)
        if inconnues:
            violations.append(f"{champ} : termes hors catalogue et hors offre : {inconnues}")
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

    base = {
        "poste": analysis.intitule or "(non précisé)",
        "entreprise": analysis.entreprise or "(non précisée)",
        "lieu": analysis.lieu or "(non précisé)",
        "contrat": analysis.type_contrat or "(non précisé)",
        "missions": "\n".join(f"- {m}" for m in analysis.missions) or "- (non précisées)",
        "requises": ", ".join(analysis.competences_requises) or "(non précisées)",
        "appreciees": ", ".join(analysis.competences_appreciees) or "(non précisées)",
        "role": selection.role,
        "projets": "\n".join(
            f"- {p.titre} ({projets[p.id].dates})\n"
            + "\n".join(f"    {b}" for b in p.bullets)
            for p in cv.projets
        ),
        "competences": "\n".join(
            f"- {catalog.categories[g.categorie]} : "
            + ", ".join(competences[i].label for i in g.skill_ids)
            for g in selection.skill_groups
        ),
        "formation": "\n".join(
            f"- {f.titre} ({f.dates}) — {f.etab}" for f in catalog.formation
        ),
        "experiences": "\n".join(
            f"- {e.titre} ({e.dates}) — {e.etab}\n" + "\n".join(f"    {b}" for b in e.bullets)
            for e in catalog.experiences
        ),
        "academique": "\n".join(
            f"- {p.titre} ({p.dates})\n"
            + "\n".join(f"    {p.bullets[i]}" for i in p.indices_defaut())
            for p in catalog.projet_academique
        ),
        "langues": " ; ".join(catalog.langues),
        "interets": ", ".join(catalog.centres_interet),
    }

    erreur: str | None = None
    for tentative in (1, 2):
        prompt = PROMPT.format(
            **base, correction=RETRY_HEADER.format(erreur=erreur) if erreur else ""
        )
        draft = provider.structured(prompt, LetterDraft, system=SYSTEM)
        violations = check_draft(draft, selection, catalog, analysis)
        if not violations:
            mots = sum(len(getattr(draft, c).split()) for c in LetterDraft.model_fields)
            LOGGER.info("Brouillon de LM accepté (%d mots)", mots)
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
    texte = (skeleton_path or SKELETON_PATH).read_text(encoding="utf-8")
    texte = re.sub(r"<!--.*?-->\n?", "", texte, flags=re.DOTALL)

    valeurs = {
        "contact_nom": catalog.contact.nom,
        "contact_email": catalog.contact.email,
        "contact_tel": catalog.contact.tel,
        "entreprise": analysis.entreprise or "",
        "lieu": analysis.lieu or "",
        "ville_expedition": VILLE_EXPEDITION,
        "date": _format_date(aujourdhui or dt.date.today()),
        "poste": analysis.intitule or "",
        "statut_lm": catalog.statut.lm.replace("{{ poste }}", analysis.intitule or ""),
        "pourquoi_entreprise": draft.pourquoi_entreprise,
        "adequation_missions": draft.adequation_missions,
        "motivation_personnelle": draft.motivation_personnelle,
        "apport_parcours": draft.apport_parcours,
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
    """Blocs [À REMPLIR PAR MARCEL] laissés dans un squelette personnalisé."""
    return PLACEHOLDER_RE.findall(markdown)
