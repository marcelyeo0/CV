# -*- coding: utf-8 -*-
"""Les CV par défaut tiennent sur 1 page et leur texte s'extrait proprement."""

from __future__ import annotations

import pytest

from cvgen.render import render_cv

LIGATURES = "ﬀﬁﬂﬃﬄﬅﬆ"


@pytest.fixture(scope="module", params=["data_analyst", "data_science_ia"])
def cv_pdf(request, catalog, tmp_path_factory):
    sortie = tmp_path_factory.mktemp("cv") / f"{request.param}.pdf"
    rapport = render_cv(catalog.selections_par_defaut[request.param], catalog, sortie)
    return rapport


def test_une_page_sans_retrait(cv_pdf):
    assert cv_pdf.pages == 1
    assert cv_pdf.removed == []


def test_extraction_propre(cv_pdf, pdftotext, catalog):
    texte = pdftotext(cv_pdf.path)

    # Une seule page : pdftotext sépare les pages par un saut de page.
    assert texte.rstrip("\f").count("\f") == 0
    assert not any(c in texte for c in LIGATURES)
    assert catalog.contact.nom in texte
    assert catalog.contact.email in texte
    assert catalog.contact.adresse_courte in texte
    for section in ("COMPETENCES", "FORMATION", "EXPERIENCE", "PROJETS MAJEURS", "LANGUES"):
        assert section in texte
