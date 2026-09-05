# -*- coding: utf-8 -*-
"""Testes do perfil (sem abrir o Spyder)."""

from setup_spyder.perfil import (
    CONF_DIRNAME,
    CONDA_ENV_VARS,
    POPUPS,
    STYLE,
    conf_dir_for,
    perfil_completo,
    resolve_hidden_paths,
    split_names,
    strip_conda_env,
)


def test_popups_matam_update_e_tour():
    assert POPUPS[("main", "check_updates_on_startup")] is False
    assert POPUPS[("tours", "show_tour_message")] is False
    assert POPUPS[("main", "show_dpi_message")] is False
    assert POPUPS[("main", "show_internal_errors")] is False
    assert POPUPS[("ipython_console", "ask_before_restart")] is False
    assert POPUPS[("main_interpreter", "default")] is True


def test_estilo_escuro():
    assert STYLE[("appearance", "ui_theme")] == "dark"
    assert STYLE[("editor", "wrap")] is True


def test_perfil_completo_com_e_sem_estilo():
    com = perfil_completo("Consolas", com_estilo=True)
    sem = perfil_completo("Consolas", com_estilo=False)
    assert ("appearance", "ui_theme") in com
    assert ("appearance", "ui_theme") not in sem
    assert com[("main", "check_updates_on_startup")] is False
    assert sem[("main", "check_updates_on_startup")] is False
    assert isinstance(com[("appearance", "font/family")], list)
    assert com[("appearance", "font/family")][0] == "Consolas"


def test_hidden_paths_inclui_venv_e_conf():
    names = resolve_hidden_paths()
    assert ".venv" in names
    assert CONF_DIRNAME in names
    assert "uv.lock" in names
    extra = resolve_hidden_paths(hide=["notes.txt"], show=[".github"])
    assert "notes.txt" in extra
    assert ".github" not in extra


def test_split_names():
    assert split_names(["a, b", "c"]) == {"a", "b", "c"}


def test_conf_dir_persistente(tmp_path):
    destino = conf_dir_for(tmp_path, ephemeral=False)
    assert destino == tmp_path / CONF_DIRNAME
    assert destino.is_dir()


def test_conf_dir_ephemeral(tmp_path):
    destino = conf_dir_for(tmp_path, ephemeral=True)
    assert destino != tmp_path / CONF_DIRNAME
    assert destino.is_dir()
    assert "setup-spyder-conf-" in destino.name
    destino.rmdir()


def test_strip_conda_env():
    env = {name: "x" for name in CONDA_ENV_VARS}
    env["PATH"] = "/usr/bin"
    limpo = strip_conda_env(env)
    assert "PATH" in limpo
    for name in CONDA_ENV_VARS:
        assert name not in limpo
