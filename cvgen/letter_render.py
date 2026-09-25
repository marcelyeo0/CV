# -*- coding: utf-8 -*-
"""Rendu PDF de la lettre de motivation à partir du brouillon Markdown relu."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from .render import RenderReport, _render_to_one_page

LOGGER = logging.getLogger(__name__)

# Le rendu refuse d'aller plus loin tant que Marcel n'a pas remplacé ces blocs.
PLACEHOLDER_RE = re.compile(r"\[À REMPLIR PAR MARCEL[^\]]*\]", re.DOTALL)

_OBJET_RE = re.compile(r"^\*\*Objet\s*:\s*(.+?)\*\*$")
_DATE_RE = re.compile(r"^(.+?),\s*le\s+(.+)$")


class LetterRenderError(Exception):
    """Brouillon inexploitable ou non relu."""


def parse_draft(markdown: str) -> dict[str, Any]:
    """Découpe le brouillon relu en blocs destinés au gabarit."""
    restants = PLACEHOLDER_RE.findall(markdown)
    if restants:
        raise LetterRenderError(
            f"{len(restants)} bloc(s) [À REMPLIR PAR MARCEL] encore présent(s) dans "
            "lm_draft.md. Les remplacer par ton texte avant de rendre la lettre."
        )

    blocs = [b.strip() for b in re.split(r"\n\s*\n", markdown.strip()) if b.strip()]
    if len(blocs) < 4:
        raise LetterRenderError("Brouillon trop court : structure de lettre non reconnue.")

    expediteur: list[str] = []
    destinataire: list[str] = []
    ville = date = poste = ""
    corps: list[str] = []
    signature_vue = False

    for index, bloc in enumerate(blocs):
        lignes = [l.strip() for l in bloc.split("\n") if l.strip()]

        if index == 0:
            expediteur = lignes
            continue
        if index == 1 and not _DATE_RE.match(lignes[0]):
            destinataire = lignes
            continue

        match_date = _DATE_RE.match(lignes[0])
        if match_date and not date:
            ville, date = match_date.group(1).strip(), match_date.group(2).strip()
            continue

        match_objet = _OBJET_RE.match(lignes[0])
        if match_objet and not poste:
            objet = match_objet.group(1)
            poste = objet.split("—", 1)[-1].strip() if "—" in objet else objet.strip()
            continue

        texte = " ".join(lignes)
        if index == len(blocs) - 1 and expediteur and texte == expediteur[0]:
            signature_vue = True
            continue
        corps.append(texte)

    if not corps:
        raise LetterRenderError("Aucun paragraphe de corps trouvé dans le brouillon.")
    if not signature_vue:
        LOGGER.warning("Signature finale absente du brouillon")

    return {
        "expediteur": expediteur,
        "destinataire": destinataire,
        "ville_expedition": ville,
        "date": date,
        "poste": poste,
        "paragraphes": corps,
    }


def _shrink_letter(context: dict[str, Any]) -> str | None:
    """Dernier recours : retirer le dernier paragraphe du corps."""
    paragraphes = context["paragraphes"]
    if len(paragraphes) > 2:
        retire = paragraphes.pop()
        return f"paragraphe de la lettre : « {retire[:80]}… »"
    return None


def render_letter(markdown: str, contact, out_path: Path | str) -> RenderReport:
    context = parse_draft(markdown)
    context["contact"] = contact
    return _render_to_one_page("letter.html.j2", context, Path(out_path), _shrink_letter)
