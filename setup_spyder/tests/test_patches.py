# -*- coding: utf-8 -*-
from setup_spyder.patches import render_launcher


def test_launcher_contem_patches():
    texto = render_launcher(["spyder", "--conf-dir", "/tmp"], [".venv", ".spyder-lab"])
    assert "sys.argv =" in texto
    assert "PATHS_TO_HIDE" in texto
    assert "find_conda" in texto
    assert "get_list_conda_envs" in texto
    assert "compute_dependencies" in texto
    assert "QApplication.beep" in texto
    assert "from spyder.app.start import main" in texto
    assert ".spyder-lab" in texto
    assert ".venv" in texto


def test_launcher_compila():
    src = render_launcher(["spyder"], [".venv"])
    compile(src, "launch_spyder.py", "exec")


def test_launcher_contem_patches():
    texto = render_launcher(["spyder", "--conf-dir", "/tmp"], [".venv", ".spyder-lab"])
    assert "sys.argv =" in texto
    assert "PATHS_TO_HIDE" in texto
    assert "find_conda" in texto
    assert "get_list_conda_envs" in texto
    assert "compute_dependencies" in texto
    assert "QApplication.beep" in texto
    assert "from spyder.app.start import main" in texto
    assert ".spyder-lab" in texto
    assert ".venv" in texto
