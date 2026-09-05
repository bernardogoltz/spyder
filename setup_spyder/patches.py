# -*- coding: utf-8 -*-
"""Script gerado e executado no processo do Spyder, antes do boot.

Tem que ser um arquivo: spyder.app.start lê sys.argv na importação, e os
patches precisam existir antes da janela ser montada.
"""

from __future__ import annotations

from typing import Sequence

LAUNCHER_TEMPLATE = '''\
"""Gerado por setup-spyder — não edite.

Aplica monkeypatches e sobe o Spyder no interpretador deste venv.
"""
import sys

# spyder.app.start lê a linha de comando na importação.
sys.argv = {argv!r}

HIDDEN = {hidden!r}

try:
    from spyder.plugins.projects.widgets.projectexplorer import ProxyModel

    ProxyModel.PATHS_TO_HIDE = sorted(
        set(getattr(ProxyModel, "PATHS_TO_HIDE", [])) | set(HIDDEN)
    )
    ProxyModel.PATHS_TO_SHOW = [
        path
        for path in getattr(ProxyModel, "PATHS_TO_SHOW", [])
        if path not in HIDDEN
    ]
except Exception as exc:  # pragma: no cover
    print(
        "setup-spyder: não deu para filtrar o painel Projetos "
        "({{exc}}); abrindo mesmo assim.".format(exc=exc),
        file=sys.stderr,
    )

try:
    import spyder.utils.conda as _conda

    _conda.find_conda = lambda pyexec=None: None
    _conda.get_list_conda_envs = lambda: {{}}
    _conda.get_list_conda_envs_cache = lambda: {{}}
except Exception:
    pass

try:
    from spyder.plugins.application.container import ApplicationContainer

    ApplicationContainer.compute_dependencies = lambda self: None
except Exception:
    pass

try:
    from qtpy.QtWidgets import QApplication

    QApplication.beep = staticmethod(lambda *a, **k: None)
except Exception:
    pass

from spyder.app.start import main

sys.exit(main())
'''


def render_launcher(argv: Sequence[str], hidden: Sequence[str]) -> str:
    return LAUNCHER_TEMPLATE.format(argv=list(argv), hidden=list(hidden))
