# -*- coding: utf-8 -*-
"""Bascule de modèle Gemini : saturation (503) et modèle retiré (404), sans réseau."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from apply.llm import GeminiProvider, LLMError


class FakeModels:
    def __init__(self, erreurs: dict[str, str]) -> None:
        self.erreurs = erreurs
        self.appels: list[str] = []

    def generate_content(self, model, contents, config):
        self.appels.append(model)
        if model in self.erreurs:
            raise RuntimeError(self.erreurs[model])
        return f"ok:{model}"


def _provider(monkeypatch, erreurs, principal="m-principal", secours="m-a,m-b"):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", secours)
    provider = GeminiProvider(api_key="test", model=principal)
    provider._client = SimpleNamespace(models=FakeModels(erreurs))
    return provider


def test_bascule_puis_rotation(monkeypatch):
    p = _provider(monkeypatch, {"m-principal": "503 UNAVAILABLE", "m-a": "404 NOT_FOUND"})
    assert p._call_with_backoff("x", None, "S") == "ok:m-b"
    assert p.model == "m-b"
    # 404 : une seule tentative ; 503 : toutes les reprises.
    assert p._client.models.appels.count("m-a") == 1
    assert p._client.models.appels.count("m-principal") == 4
    assert p.fallback_models == ["m-a", "m-principal"]


def test_erreur_de_requete_sans_bascule(monkeypatch):
    p = _provider(monkeypatch, {"m-principal": "400 INVALID_ARGUMENT"})
    with pytest.raises(LLMError):
        p._call_with_backoff("x", None, "S")
    assert p._client.models.appels == ["m-principal"]


def test_tous_satures(monkeypatch):
    erreurs = {m: "503 UNAVAILABLE" for m in ("m-principal", "m-a", "m-b")}
    p = _provider(monkeypatch, erreurs)
    with pytest.raises(LLMError):
        p._call_with_backoff("x", None, "S")
