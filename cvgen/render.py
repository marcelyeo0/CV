# -*- coding: utf-8 -*-
"""Rendu PDF d'une `Selection` : HTML Jinja2 autoéchappé -> WeasyPrint, 1 page garantie."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from weasyprint import HTML

from .catalog import resolve, validate_selection
from .models import Catalog, Selection

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
FONTS_DIR = ROOT / "assets" / "fonts"

NAVY = "#2e3e4e"

# Taille de base. Latin Modern est plus étroit qu'Arial : valeur calée pour que
# les deux sélections par défaut tiennent sur 1 page sans aucun retrait.
BASE_PX = 11.6

MIN_PROJETS = 1
MIN_BULLETS_PAR_PROJET = 1
MIN_CENTRES_INTERET = 2
MAX_PASSES = 40


class RenderPageError(Exception):
    """Impossible de tenir sur une page sans descendre sous le contenu minimal."""


@dataclass
class RenderReport:
    path: Path
    pages: int
    removed: list[str] = field(default_factory=list)


def _environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(
            enabled_extensions=("html", "j2", "css"),
            default_for_string=True,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Réservé aux chaînes du catalogue et à notre propre CSS ; jamais au texte
    # produit par le LLM ou extrait de l'offre.
    env.filters["safe_markup"] = Markup
    return env


def _css(env: Environment, base_px: float = BASE_PX) -> str:
    # file:// pour que WeasyPrint résolve les polices sous Windows.
    fonts_url = FONTS_DIR.as_uri()
    return env.get_template("base.css").render(fonts_dir=fonts_url, navy=NAVY, base_px=base_px)


def _cv_context(selection: Selection, catalog: Catalog) -> dict[str, Any]:
    cv = resolve(selection, catalog)
    return {
        "contact": catalog.contact,
        "tagline": cv.tagline,
        "skill_groups": [
            {"label": g.label, "ligne": g.ligne} for g in cv.skill_groups
        ],
        "formation": list(catalog.formation),
        "experiences": list(catalog.experiences),
        "projets": [
            {"id": p.id, "titre": p.titre, "dates": p.dates, "bullets": list(p.bullets)}
            for p in cv.projets
        ],
        "projet_academique": [
            {"titre": p.titre, "dates": p.dates, "bullets": list(p.bullets)}
            for p in catalog.projet_academique
        ],
        "langues": list(catalog.langues),
        "centres_interet": list(catalog.centres_interet),
    }


def _shrink_cv(context: dict[str, Any]) -> str | None:
    """Retire l'élément le moins prioritaire. Renvoie sa description, ou None."""
    projets = context["projets"]

    for projet in reversed(projets):
        if len(projet["bullets"]) > MIN_BULLETS_PAR_PROJET:
            dropped = projet["bullets"].pop()
            return f"puce du projet '{projet['titre']}' : « {dropped} »"

    if len(projets) > MIN_PROJETS:
        dropped = projets.pop()
        return f"projet '{dropped['titre']}'"

    centres = context["centres_interet"]
    if len(centres) > MIN_CENTRES_INTERET:
        return f"centre d'intérêt « {centres.pop()} »"

    return None


def render_html(
    template_name: str,
    context: dict[str, Any],
    env: Environment | None = None,
    base_px: float = BASE_PX,
) -> str:
    env = env or _environment()
    return env.get_template(template_name).render(css=_css(env, base_px), **context)


def _render_to_one_page(
    template_name: str,
    context: dict[str, Any],
    out_path: Path,
    shrink,
) -> RenderReport:
    env = _environment()
    removed: list[str] = []

    for _ in range(MAX_PASSES):
        html = render_html(template_name, context, env)
        document = HTML(string=html, base_url=str(ROOT)).render()
        pages = len(document.pages)

        if pages == 1:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            document.write_pdf(out_path)
            return RenderReport(path=out_path, pages=pages, removed=removed)

        dropped = shrink(context)
        if dropped is None:
            raise RenderPageError(
                f"{out_path.name} tient sur {pages} pages et le contenu minimal est atteint ; "
                "raccourcir les puces du catalogue ou réduire la sélection."
            )
        LOGGER.warning("1 page dépassée (%d) — retiré : %s", pages, dropped)
        removed.append(dropped)

    raise RenderPageError(f"{out_path.name} : réduction sans convergence après {MAX_PASSES} passes")


def render_cv(selection: Selection, catalog: Catalog, out_path: Path | str) -> RenderReport:
    """Valide puis rend le CV. Les retraits éventuels sont journalisés et rapportés."""
    selection = validate_selection(selection, catalog, strict=False)
    context = _cv_context(selection, catalog)
    return _render_to_one_page("cv.html.j2", context, Path(out_path), _shrink_cv)
