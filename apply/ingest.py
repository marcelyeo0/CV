# -*- coding: utf-8 -*-
"""Récupération du texte d'une offre : fichier, stdin, ou URL en best effort."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOGGER = logging.getLogger(__name__)

# En dessous, on considère qu'on n'a pas récupéré l'offre mais un bandeau de
# cookies, une page de connexion ou un squelette JS.
MIN_CHARS = 400

_COLLER = (
    "Copier le texte de l'offre dans un fichier, puis relancer avec "
    "`--text offre.txt` (ou coller sur l'entrée standard avec `--text -`)."
)


class IngestError(Exception):
    """Texte d'offre indisponible ou inexploitable."""


def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            cleaned.append(line)
        else:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()


def _check_length(text: str, origine: str) -> str:
    if len(text) < MIN_CHARS:
        raise IngestError(
            f"Texte récupéré trop court ({len(text)} caractères, minimum {MIN_CHARS}) "
            f"depuis {origine}. " + _COLLER
        )
    return text


def from_text_file(path: Path | str) -> str:
    """Lit un fichier texte, ou stdin si le chemin est '-'."""
    if str(path) == "-":
        raw = sys.stdin.read()
        origine = "l'entrée standard"
    else:
        path = Path(path)
        if not path.is_file():
            raise IngestError(f"Fichier introuvable : {path}")
        raw = path.read_text(encoding="utf-8", errors="replace")
        origine = str(path)
    return _check_length(_normalize(raw), origine)


def from_url(url: str) -> str:
    """Extraction best effort. Aucun contournement de protection anti-bot."""
    try:
        import trafilatura
    except ImportError as exc:  # pragma: no cover
        raise IngestError(f"trafilatura n'est pas installé : {exc}. " + _COLLER) from exc

    LOGGER.info("Téléchargement de %s", url)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise IngestError(
            f"Page inaccessible : {url}\n"
            "Beaucoup de sites d'emploi (LinkedIn, Indeed, pages rendues en JS, pages "
            "derrière connexion) bloquent la récupération automatique. " + _COLLER
        )

    extracted = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if not extracted:
        raise IngestError(
            f"Aucun texte exploitable extrait de {url} (page probablement rendue en "
            "JavaScript). " + _COLLER
        )

    return _check_length(_normalize(extracted), url)


def read_offer(text_path: Path | str | None = None, url: str | None = None) -> str:
    """Voie principale : le texte. L'URL n'est qu'un raccourci best effort."""
    if bool(text_path) == bool(url):
        raise IngestError("Fournir exactement une source : --text ou --url.")
    return from_text_file(text_path) if text_path else from_url(url)  # type: ignore[arg-type]
