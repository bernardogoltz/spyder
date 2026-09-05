# -*- coding: utf-8 -*-
import os

from setup_spyder.prereq import diagnose_prerequisites


def test_diagnose_sem_cli_e_sem_chave(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("setup_spyder.prereq.shutil.which", lambda name: None)
    avisos = diagnose_prerequisites("")
    assert any("claude" in a for a in avisos)
    assert any("ANTHROPIC_API_KEY" in a for a in avisos)


def test_diagnose_ok(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    avisos = diagnose_prerequisites(cli_path=os.path.abspath(__file__))
    assert avisos == []
