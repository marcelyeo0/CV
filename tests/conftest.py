# -*- coding: utf-8 -*-
"""Fixtures communes : catalogue réel et extraction de texte via pdftotext."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cvgen.catalog import load_catalog  # noqa: E402


@pytest.fixture(scope="session")
def catalog():
    return load_catalog()


@pytest.fixture(scope="session")
def pdftotext():
    """Texte extrait d'un PDF, comme le ferait un parseur ATS."""
    exe = shutil.which("pdftotext")
    if exe is None:
        pytest.skip("pdftotext (poppler) introuvable dans le PATH")

    def extraire(pdf: Path) -> str:
        sortie = subprocess.run(
            [exe, "-enc", "UTF-8", str(pdf), "-"], capture_output=True, check=True
        )
        return sortie.stdout.decode("utf-8")

    return extraire
