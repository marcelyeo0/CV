# -*- coding: utf-8 -*-
"""CLI en deux temps : `prepare` propose, `render` produit les PDF après relecture.

Aucun PDF n'est produit sans qu'un `selection.json` existe sur le disque, donc sans
que la sélection ait pu être relue.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / "src" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
DEPENDANCES = ("weasyprint", "jinja2", "pydantic", "yaml", "google.genai", "dotenv", "trafilatura")


def _modules_manquants() -> list[str]:
    manquants = []
    for nom in DEPENDANCES:
        try:
            if importlib.util.find_spec(nom) is None:
                manquants.append(nom)
        except ModuleNotFoundError:  # parent absent, ex. google pour google.genai
            manquants.append(nom)
    return manquants


def _relancer_dans_venv() -> None:
    """Lancé avec un Python sans les dépendances : on repasse par src/.venv."""
    manquants = _modules_manquants()
    if not manquants:
        return
    dans_venv = Path(sys.prefix).resolve() == VENV_PYTHON.parent.parent.resolve()
    if VENV_PYTHON.is_file() and not dans_venv:
        code = subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])
        sys.exit(code)
    sys.exit(
        f"Modules manquants pour {sys.executable} : {', '.join(manquants)}\n"
        f"  {VENV_PYTHON if VENV_PYTHON.is_file() else sys.executable} -m pip install -r "
        f"{ROOT / 'requirements.txt'}"
    )


if __name__ == "__main__":
    _relancer_dans_venv()

from apply.analyze import analyze_offer  # noqa: E402
from apply.ingest import IngestError, read_offer
from apply.letter import LetterError, build_draft, fill_skeleton, remaining_placeholders
from apply.llm import GeminiProvider, LLMError, LLMProvider
from apply.select import build_selection
from cvgen.catalog import SelectionError, load_catalog
from cvgen.letter_render import LetterRenderError, render_letter
from cvgen.models import Catalog, OfferAnalysis, Selection
from cvgen.render import RenderPageError, render_cv

OUTPUTS = ROOT / "outputs"

LOGGER = logging.getLogger("cv")


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slugify(texte: str, defaut: str = "inconnu", max_len: int = 40) -> str:
    """ASCII, sans accent ni espace : utilisable en nom de dossier et de fichier."""
    decompose = unicodedata.normalize("NFKD", texte)
    ascii_only = "".join(c for c in decompose if not unicodedata.combining(c))
    ascii_only = ascii_only.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_only).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) > max_len:
        # Coupe sur un séparateur plutôt qu'au milieu d'un mot.
        coupe = slug[:max_len]
        if "-" in coupe:
            coupe = coupe.rsplit("-", 1)[0]
        slug = coupe
    return slug.strip("-") or defaut


# Sigles à garder en capitales dans les noms de fichiers des CV génériques.
ACRONYMES = {"ia", "ai", "ml", "nlp", "bi", "cv", "llm"}


def _variante_fichier(cle: str) -> str:
    """data_science_ia -> Data_Science_IA"""
    return "_".join(m.upper() if m in ACRONYMES else m.capitalize() for m in cle.split("_"))


def _dump_json(path: Path, model) -> None:
    path.write_text(
        json.dumps(model.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_json(path: Path, model_cls):
    if not path.is_file():
        raise SystemExit(f"Fichier manquant : {path}")
    return model_cls.model_validate_json(path.read_text(encoding="utf-8"))


def _provider() -> LLMProvider:
    try:
        return GeminiProvider()
    except LLMError as exc:
        raise SystemExit(str(exc)) from exc


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def _resume(analysis: OfferAnalysis, selection: Selection, catalog: Catalog,
            dossier: Path, avertissements: list[str]) -> None:
    projets = {p.id: p for p in catalog.projets}
    competences = {c.id: c for c in catalog.competences}

    print()
    print("=" * 78)
    print(f"  {analysis.intitule or '(intitulé inconnu)'}")
    print(f"  {analysis.entreprise or '(entreprise inconnue)'} — {analysis.lieu or '(lieu inconnu)'}")
    print(f"  {analysis.type_contrat or '(contrat non précisé)'} — offre en {analysis.langue}")
    print("=" * 78)

    print(f"\nIntitulé ciblé sur le CV : {selection.role}")
    print(f"Tagline rendue           : {catalog.disponibilite.tagline(selection.role)}")

    print("\nProjets retenus :")
    for rang, projet_id in enumerate(selection.project_ids, 1):
        projet = projets[projet_id]
        indices = selection.bullet_selection.get(projet_id) or projet.indices_defaut()
        print(f"  {rang}. {projet.titre}  ({projet.dates})")
        for i in indices:
            print(f"       - {projet.bullets[i]}")

    print("\nCompétences, dans l'ordre d'affichage :")
    for groupe in selection.skill_groups:
        libelles = ", ".join(competences[i].label for i in groupe.skill_ids)
        print(f"  {catalog.categories[groupe.categorie]} : {libelles}")

    if selection.bullet_overrides:
        print("\nPuces reformulées :")
        for o in selection.bullet_overrides:
            print(f"  {o.projet_id}[{o.index}]")
            print(f"    origine : {projets[o.projet_id].bullets[o.index]}")
            print(f"    retenue : {o.texte}")

    if selection.justification:
        print(f"\nJustification : {selection.justification}")

    if selection.missing_keywords:
        print("\nMots-clés de l'offre absents de ton catalogue :")
        for mot in selection.missing_keywords:
            print(f"  - {mot}")
        print("  (à toi de décider si tu les ajoutes — honnêtement, jamais automatiquement)")

    for message in avertissements:
        print(f"\nATTENTION : {message}")

    print(f"\nDossier : {dossier}")
    print("Relis et corrige selection.json et lm_draft.md, puis rends les PDF :")
    print(f'  python main.py render "{dossier.relative_to(ROOT).as_posix()}"')
    print()


def cmd_prepare(args: argparse.Namespace) -> int:
    catalog = load_catalog()

    try:
        offre = read_offer(text_path=args.text, url=args.url)
    except IngestError as exc:
        print(f"ERREUR d'ingestion : {exc}", file=sys.stderr)
        return 2

    provider = _provider()

    try:
        analysis = analyze_offer(offre, provider)
    except LLMError as exc:
        print(f"ERREUR d'analyse : {exc}", file=sys.stderr)
        return 3

    avertissements: list[str] = []
    if analysis.langue != "fr":
        avertissements.append(
            f"L'offre est en '{analysis.langue}'. La lettre reste en français et le CV "
            "n'est pas traduit."
        )

    try:
        selection = build_selection(analysis, catalog, provider)
    except (SelectionError, LLMError) as exc:
        print(f"ERREUR de sélection : {exc}", file=sys.stderr)
        return 3

    dossier = OUTPUTS / "_".join([
        dt.date.today().isoformat(),
        slugify(analysis.entreprise, "entreprise"),
        slugify(analysis.intitule, "poste"),
    ])
    dossier.mkdir(parents=True, exist_ok=True)

    (dossier / "offre.txt").write_text(offre, encoding="utf-8")
    _dump_json(dossier / "analysis.json", analysis)
    _dump_json(dossier / "selection.json", selection)

    code = _ecrire_lettre(analysis, selection, catalog, provider, dossier, avertissements)
    if code:
        return code

    _resume(analysis, selection, catalog, dossier, avertissements)
    return 0


def _ecrire_lettre(analysis: OfferAnalysis, selection: Selection, catalog: Catalog,
                   provider: LLMProvider, dossier: Path, avertissements: list[str]) -> int:
    try:
        draft = build_draft(analysis, selection, catalog, provider)
    except (LetterError, LLMError) as exc:
        print(f"ERREUR de rédaction de la lettre : {exc}", file=sys.stderr)
        rel = dossier.relative_to(ROOT).as_posix() if dossier.is_relative_to(ROOT) else dossier
        print(f"Le CV reste générable : offre.txt, analysis.json et selection.json sont "
              f"écrits dans {dossier}\n"
              f"Relancer la lettre seule, plus tard :\n"
              f'  python main.py lettre "{rel}"', file=sys.stderr)
        return 4
    markdown = fill_skeleton(draft, analysis, catalog)
    (dossier / "lm_draft.md").write_text(markdown, encoding="utf-8")

    restants = remaining_placeholders(markdown)
    if restants:
        avertissements.append(
            f"{len(restants)} bloc(s) [À REMPLIR PAR MARCEL] dans lm_draft.md : le rendu de "
            "la lettre échouera tant qu'ils y sont."
        )
    avertissements.append(
        "Dans lm_draft.md, les paragraphes « motivation personnelle » (3e) et "
        "« apport du parcours » (4e) sont des PROPOSITIONS : le LLM ne connaît pas tes "
        "raisons réelles, il compose à partir du catalogue. Relis-les et réécris-les avant "
        "d'envoyer — c'est ce que tu devras défendre en entretien."
    )
    return 0


def _dossier_existant(brut: str) -> Path | None:
    dossier = Path(brut)
    if not dossier.is_absolute():
        dossier = (ROOT / dossier).resolve()
    if not dossier.is_dir():
        print(f"Dossier introuvable : {dossier}", file=sys.stderr)
        return None
    return dossier


def cmd_lettre(args: argparse.Namespace) -> int:
    """Rédige lm_draft.md à partir d'un dossier déjà préparé, sans refaire l'analyse."""
    dossier = _dossier_existant(args.dossier)
    if dossier is None:
        return 2
    draft_path = dossier / "lm_draft.md"
    if draft_path.is_file() and not args.force:
        print(f"{draft_path} existe déjà (peut-être relu). --force pour l'écraser.",
              file=sys.stderr)
        return 2

    catalog = load_catalog()
    analysis: OfferAnalysis = _load_json(dossier / "analysis.json", OfferAnalysis)
    selection: Selection = _load_json(dossier / "selection.json", Selection)

    avertissements: list[str] = []
    code = _ecrire_lettre(analysis, selection, catalog, _provider(), dossier, avertissements)
    if code:
        return code
    for message in avertissements:
        print(f"ATTENTION : {message}")
    print(f"\n{draft_path.name} écrit. Relis-le, puis :")
    print(f'  python main.py render "{dossier.relative_to(ROOT).as_posix()}"')
    return 0


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def _render_defaults(catalog: Catalog, nom: str) -> int:
    cibles = list(catalog.selections_par_defaut) if nom == "all" else [nom]
    inconnues = [c for c in cibles if c not in catalog.selections_par_defaut]
    if inconnues:
        print(f"Sélection par défaut inconnue : {inconnues}. "
              f"Disponibles : {list(catalog.selections_par_defaut)} ou 'all'", file=sys.stderr)
        return 2

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for cle in cibles:
        sortie = OUTPUTS / f"CV_Marcel_Yeo_{_variante_fichier(cle)}.pdf"
        rapport = render_cv(catalog.selections_par_defaut[cle], catalog, sortie)
        print(f"{sortie.name}  ({rapport.pages} page)")
        for retire in rapport.removed:
            print(f"    retiré pour tenir sur 1 page : {retire}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    catalog = load_catalog()

    if args.default:
        return _render_defaults(catalog, args.default)

    if not args.dossier:
        print("Indiquer un dossier, ou --default <variante>", file=sys.stderr)
        return 2

    dossier = _dossier_existant(args.dossier)
    if dossier is None:
        return 2

    analysis: OfferAnalysis = _load_json(dossier / "analysis.json", OfferAnalysis)
    selection: Selection = _load_json(dossier / "selection.json", Selection)

    poste = slugify(selection.role or analysis.intitule, "Poste")
    entreprise = slugify(analysis.entreprise, "Entreprise")

    cv_path = dossier / f"CV_Marcel_Yeo_{poste}.pdf"
    try:
        rapport = render_cv(selection, catalog, cv_path)
    except (SelectionError, RenderPageError) as exc:
        print(f"ERREUR de rendu du CV : {exc}", file=sys.stderr)
        return 3
    print(f"{cv_path.name}  ({rapport.pages} page)")
    for retire in rapport.removed:
        print(f"    retiré pour tenir sur 1 page : {retire}")

    draft_path = dossier / "lm_draft.md"
    if not draft_path.is_file():
        print(f"Pas de lm_draft.md dans {dossier} : lettre non rendue.")
        return 0

    lm_path = dossier / f"LM_Marcel_Yeo_{entreprise}.pdf"
    try:
        rapport = render_letter(draft_path.read_text(encoding="utf-8"), catalog.contact, lm_path)
    except (LetterRenderError, RenderPageError) as exc:
        print(f"ERREUR de rendu de la lettre : {exc}", file=sys.stderr)
        return 4
    print(f"{lm_path.name}  ({rapport.pages} page)")
    for retire in rapport.removed:
        print(f"    retiré pour tenir sur 1 page : {retire}")

    return 0


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Génère un CV ATS et une lettre de motivation ciblés."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="journal détaillé")
    sub = parser.add_subparsers(dest="commande", required=True)

    prepare = sub.add_parser(
        "prepare", help="analyse une offre et propose une sélection (ne rend aucun PDF)"
    )
    source = prepare.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", metavar="FICHIER", help="fichier texte de l'offre, ou - pour stdin")
    source.add_argument("--url", metavar="URL", help="URL de l'offre (best effort)")
    prepare.set_defaults(func=cmd_prepare)

    lettre = sub.add_parser(
        "lettre", help="rédige seulement lm_draft.md depuis un dossier créé par prepare"
    )
    lettre.add_argument("dossier", help="dossier créé par prepare")
    lettre.add_argument("--force", action="store_true", help="écrase un lm_draft.md existant")
    lettre.set_defaults(func=cmd_lettre)

    render = sub.add_parser("render", help="produit les PDF depuis un dossier relu")
    render.add_argument("dossier", nargs="?", help="dossier créé par prepare")
    render.add_argument("--default", metavar="VARIANTE",
                        help="régénère un CV générique : data_analyst, data_science_ia, all")
    render.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("weasyprint").setLevel(logging.ERROR)
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
