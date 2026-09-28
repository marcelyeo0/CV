# -*- coding: utf-8 -*-
"""L'adresse postale n'apparaît ni dans le contexte LLM, ni dans le brouillon, ni dans le PDF."""

from __future__ import annotations

import datetime as dt
import re

import pytest

from apply.letter import build_draft, fill_skeleton
from cvgen.letter_render import render_letter
from cvgen.models import LetterDraft, OfferAnalysis


class FakeProvider:
    """Renvoie un brouillon fixe et garde tout ce qui aurait été envoyé au LLM."""

    def __init__(self) -> None:
        self.envois: list[str] = []

    def structured(self, prompt, schema, system=""):
        self.envois += [prompt, system]
        return LetterDraft(
            pourquoi_entreprise="le poste porte sur l'analyse des ventes par circuit.",
            adequation_missions="les missions recoupent les projets retenus sur le cv.",
            motivation_personnelle="ce travail relie la donnée brute à une décision concrète.",
            apport_parcours="la formation suivie apporte une base solide en statistiques.",
        )


@pytest.fixture(scope="module")
def adresse(catalog):
    """Numéro, nom de rue et code postal de l'adresse du catalogue."""
    complete = catalog.contact.adresse
    numero = re.match(r"\s*(\d+)", complete).group(1)
    code_postal = re.search(r"\b(\d{5})\b", complete).group(1)
    rue = complete.split(",")[0][len(numero):].strip()
    return {"numero": numero, "rue": rue, "code_postal": code_postal}


@pytest.fixture(scope="module")
def analysis():
    return OfferAnalysis(
        intitule="Data Analyst", entreprise="Exemple SA", lieu="Lyon",
        missions=["analyser les ventes"],
    )


def _absente(texte: str, adresse: dict[str, str]) -> None:
    assert not re.search(rf"\b{adresse['numero']}\b", texte), "numéro de rue présent"
    assert adresse["rue"] not in texte, "nom de rue présent"
    assert adresse["code_postal"] not in texte, "code postal présent"


def test_adresse_absente_du_contexte_llm(catalog, analysis, adresse):
    provider = FakeProvider()
    build_draft(analysis, catalog.selections_par_defaut["data_analyst"], catalog, provider)
    assert provider.envois
    _absente("\n".join(provider.envois), adresse)


def test_adresse_absente_du_pdf(catalog, analysis, adresse, pdftotext, tmp_path):
    selection = catalog.selections_par_defaut["data_analyst"]
    draft = build_draft(analysis, selection, catalog, FakeProvider())
    markdown = fill_skeleton(draft, analysis, catalog, aujourdhui=dt.date(2026, 9, 28))
    _absente(markdown, adresse)

    rapport = render_letter(markdown, catalog.contact, tmp_path / "lm.pdf")
    texte = pdftotext(rapport.path)
    _absente(texte, adresse)
    for garde in (catalog.contact.nom, catalog.contact.email, catalog.contact.tel):
        assert garde in texte


def test_ancien_brouillon_avec_adresse_filtre(catalog, analysis, adresse, pdftotext, tmp_path):
    draft = build_draft(analysis, catalog.selections_par_defaut["data_analyst"], catalog,
                        FakeProvider())
    markdown = fill_skeleton(draft, analysis, catalog)
    ancien = markdown.replace(catalog.contact.nom + "\n",
                              f"{catalog.contact.nom}\n{catalog.contact.adresse}\n", 1)
    assert catalog.contact.adresse in ancien

    rapport = render_letter(ancien, catalog.contact, tmp_path / "lm.pdf")
    _absente(pdftotext(rapport.path), adresse)
