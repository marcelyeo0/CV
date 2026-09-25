# -*- coding: utf-8 -*-
"""Chargement du catalogue, liste blanche des technos et validation stricte des sélections."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

from .models import (
    Catalog,
    Competence,
    Projet,
    Selection,
    normalize,
    numbers,
    tech_tokens,
)

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "catalog.yaml"

MAX_PROJECTS = 3

# Une tagline ne doit jamais porter la disponibilité : elle vient du catalogue.
_DATE_IN_ROLE_RE = re.compile(
    r"\b(\d{4}|\d\s*-\s*\d\s*mois|\d+\s*mois|janvier|f[ée]vrier|mars|avril|mai|juin|"
    r"juillet|ao[uû]t|septembre|octobre|novembre|d[ée]cembre|stage|alternance)\b",
    re.IGNORECASE,
)


class CatalogError(Exception):
    """Catalogue incohérent."""


class SelectionError(Exception):
    """Sélection invalide au regard du catalogue."""


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

def load_catalog(path: Path | str | None = None) -> Catalog:
    path = Path(path) if path is not None else CATALOG_PATH
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    catalog = Catalog.model_validate(raw)
    _check_catalog_integrity(catalog)
    return catalog


def _check_catalog_integrity(catalog: Catalog) -> None:
    problems: list[str] = []

    for label, items in (
        ("projets", catalog.projets),
        ("projet_academique", catalog.projet_academique),
        ("experiences", catalog.experiences),
        ("competences", catalog.competences),
    ):
        ids = [item.id for item in items]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            problems.append(f"{label} : ids dupliqués {sorted(duplicates)}")

    for competence in catalog.competences:
        unknown = set(competence.categories) - set(catalog.categories)
        if unknown:
            problems.append(f"compétence '{competence.id}' : catégories inconnues {sorted(unknown)}")

    for projet in catalog.projets + catalog.projet_academique:
        for index in projet.indices_defaut():
            if not 0 <= index < len(projet.bullets):
                problems.append(f"projet '{projet.id}' : bullets_defaut hors bornes ({index})")

    for name, selection in catalog.selections_par_defaut.items():
        try:
            validate_selection(selection, catalog, strict=True)
        except SelectionError as exc:
            problems.append(f"sélection par défaut '{name}' : {exc}")

    if problems:
        raise CatalogError("Catalogue invalide :\n- " + "\n- ".join(problems))


# ---------------------------------------------------------------------------
# Index et liste blanche
# ---------------------------------------------------------------------------

def projet_index(catalog: Catalog) -> dict[str, Projet]:
    return {p.id: p for p in catalog.projets + catalog.projet_academique}


def competence_index(catalog: Catalog) -> dict[str, Competence]:
    return {c.id: c for c in catalog.competences}


def _catalog_texts(catalog: Catalog) -> Iterable[str]:
    for competence in catalog.competences:
        yield competence.label
        yield " ".join(competence.tags)
    for projet in catalog.projets + catalog.projet_academique:
        yield projet.titre
        yield " ".join(projet.tags)
        yield from projet.bullets
    for experience in catalog.experiences:
        yield experience.titre
        yield experience.etab
        yield from experience.bullets
    for formation in catalog.formation:
        yield formation.titre
        yield formation.etab
    yield from catalog.langues
    yield from catalog.centres_interet


def tech_whitelist(catalog: Catalog) -> set[str]:
    """Tous les tokens techno-formés présents quelque part dans le catalogue."""
    allowed: set[str] = set()
    for text in _catalog_texts(catalog):
        allowed |= tech_tokens(text)
    # Les tags sont des identifiants (kebab-case) : on autorise aussi leurs segments.
    for competence in catalog.competences:
        for tag in competence.tags:
            allowed |= {normalize(part) for part in tag.split("-") if part}
    for projet in catalog.projets + catalog.projet_academique:
        for tag in projet.tags:
            allowed |= {normalize(part) for part in tag.split("-") if part}
    allowed.discard("")
    return allowed


def check_rewrite(original: str, rewrite: str, allowed: set[str]) -> list[str]:
    """Renvoie la liste des violations d'un texte reformulé (vide si conforme)."""
    violations: list[str] = []

    unknown = sorted(tech_tokens(rewrite) - allowed - tech_tokens(original))
    if unknown:
        violations.append(f"techno(s) hors catalogue : {unknown}")

    new_numbers = sorted(numbers(rewrite) - numbers(original))
    if new_numbers:
        violations.append(f"chiffre(s) inédit(s) : {new_numbers}")

    return violations


# ---------------------------------------------------------------------------
# Validation d'une sélection
# ---------------------------------------------------------------------------

def validate_selection(selection: Selection, catalog: Catalog, *, strict: bool = True) -> Selection:
    """Valide une sélection contre le catalogue.

    strict=True  : toute violation lève `SelectionError`.
    strict=False : les `bullet_overrides` fautifs sont écartés (la puce d'origine
                   est conservée) et journalisés ; le reste lève toujours.
    """
    projets = projet_index(catalog)
    competences = competence_index(catalog)
    errors: list[str] = []

    # -- projets
    if len(selection.project_ids) > MAX_PROJECTS:
        errors.append(f"{len(selection.project_ids)} projets sélectionnés, maximum {MAX_PROJECTS}")
    duplicates = {i for i in selection.project_ids if selection.project_ids.count(i) > 1}
    if duplicates:
        errors.append(f"projets en double : {sorted(duplicates)}")
    unknown_projects = [i for i in selection.project_ids if i not in projets]
    if unknown_projects:
        errors.append(f"project_ids inconnus : {unknown_projects}")

    # -- compétences
    for group in selection.skill_groups:
        if group.categorie not in catalog.categories:
            errors.append(f"catégorie inconnue : '{group.categorie}'")
        seen_ids: set[str] = set()
        seen_groupes: set[str] = set()
        for skill_id in group.skill_ids:
            competence = competences.get(skill_id)
            if competence is None:
                errors.append(f"skill_id inconnu : '{skill_id}'")
                continue
            if skill_id in seen_ids:
                errors.append(f"compétence '{skill_id}' en double dans '{group.categorie}'")
            seen_ids.add(skill_id)
            if competence.groupe in seen_groupes:
                errors.append(
                    f"deux formulations de '{competence.groupe}' dans '{group.categorie}'"
                )
            seen_groupes.add(competence.groupe)
            if group.categorie in catalog.categories and group.categorie not in competence.categories:
                errors.append(
                    f"compétence '{skill_id}' non autorisée dans la catégorie '{group.categorie}'"
                )

    # -- sélection de puces
    for projet_id, indices in selection.bullet_selection.items():
        projet = projets.get(projet_id)
        if projet is None:
            errors.append(f"bullet_selection : projet inconnu '{projet_id}'")
            continue
        if projet_id not in selection.project_ids:
            errors.append(f"bullet_selection : projet non sélectionné '{projet_id}'")
        if not indices:
            errors.append(f"bullet_selection : aucune puce retenue pour '{projet_id}'")
        for index in indices:
            if not 0 <= index < len(projet.bullets):
                errors.append(f"bullet_selection : index {index} hors bornes pour '{projet_id}'")

    # -- reformulations
    allowed = tech_whitelist(catalog)
    kept_overrides = []
    for override in selection.bullet_overrides:
        projet = projets.get(override.projet_id)
        if projet is None:
            errors.append(f"bullet_override : projet inconnu '{override.projet_id}'")
            continue
        if override.projet_id not in selection.project_ids:
            errors.append(f"bullet_override : projet non sélectionné '{override.projet_id}'")
            continue
        if not 0 <= override.index < len(projet.bullets):
            errors.append(
                f"bullet_override : index {override.index} hors bornes pour '{override.projet_id}'"
            )
            continue
        violations = check_rewrite(projet.bullets[override.index], override.texte, allowed)
        if violations:
            message = (
                f"bullet_override {override.projet_id}[{override.index}] rejeté : "
                + " ; ".join(violations)
            )
            if strict:
                errors.append(message)
            else:
                LOGGER.warning("%s — puce d'origine conservée", message)
            continue
        kept_overrides.append(override)

    # -- tagline
    if _DATE_IN_ROLE_RE.search(selection.role):
        errors.append(
            f"role '{selection.role}' contient une date ou une durée : "
            "la disponibilité vient du catalogue"
        )

    if errors:
        raise SelectionError("; ".join(errors))

    if len(kept_overrides) != len(selection.bullet_overrides):
        return selection.model_copy(update={"bullet_overrides": kept_overrides})
    return selection


# ---------------------------------------------------------------------------
# Résolution : sélection -> structure prête à rendre
# ---------------------------------------------------------------------------

@dataclass
class ResolvedProjet:
    id: str
    titre: str
    dates: str
    bullets: list[str]


@dataclass
class ResolvedGroup:
    categorie: str
    label: str
    items: list[str]

    @property
    def ligne(self) -> str:
        return ", ".join(self.items)


@dataclass
class ResolvedCV:
    tagline: str
    skill_groups: list[ResolvedGroup] = field(default_factory=list)
    projets: list[ResolvedProjet] = field(default_factory=list)


def resolve(selection: Selection, catalog: Catalog) -> ResolvedCV:
    """Traduit une sélection validée en contenu prêt à rendre."""
    projets = projet_index(catalog)
    competences = competence_index(catalog)

    groups = [
        ResolvedGroup(
            categorie=group.categorie,
            label=catalog.categories[group.categorie],
            items=[competences[skill_id].label for skill_id in group.skill_ids],
        )
        for group in selection.skill_groups
    ]

    overrides = {(o.projet_id, o.index): o.texte for o in selection.bullet_overrides}
    resolved_projets = []
    for projet_id in selection.project_ids:
        projet = projets[projet_id]
        indices = selection.bullet_selection.get(projet_id) or projet.indices_defaut()
        resolved_projets.append(
            ResolvedProjet(
                id=projet.id,
                titre=projet.titre,
                dates=projet.dates,
                bullets=[overrides.get((projet_id, i), projet.bullets[i]) for i in indices],
            )
        )

    return ResolvedCV(
        tagline=catalog.disponibilite.tagline(selection.role),
        skill_groups=groups,
        projets=resolved_projets,
    )
