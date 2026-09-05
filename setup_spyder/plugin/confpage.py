# -*- coding: utf-8 -*-
"""Página em Preferências do plugin Claude Code."""

from __future__ import annotations

from qtpy.QtWidgets import QGroupBox, QVBoxLayout

from spyder.api.preferences import PluginConfigPage
from spyder.api.translations import _

from setup_spyder.plugin.api import EFFORT_LEVELS, MODELOS, PERMISSION_MODES


class ClaudeCodeConfPage(PluginConfigPage):

    def setup_page(self):
        grupo = QGroupBox(_("Claude Code"))

        modelo = self.create_combobox(_("Modelo"), MODELOS, "model")
        perms = self.create_combobox(
            _("Permissões"), PERMISSION_MODES, "permission_mode"
        )
        effort = self.create_combobox(_("Esforço"), EFFORT_LEVELS, "effort")
        anexar = self.create_checkbox(
            _("Anexar arquivo/seleção atual ao prompt"), "anexar_selecao"
        )
        cli = self.create_lineedit(
            _("Caminho do CLI claude (vazio = PATH)"), "cli_path"
        )
        extras = self.create_lineedit(
            _("Diretórios extras (--add-dir), separados por ;"), "add_dirs"
        )

        layout_grupo = QVBoxLayout()
        for widget in (modelo, perms, effort, anexar, cli, extras):
            layout_grupo.addWidget(widget)
        grupo.setLayout(layout_grupo)

        layout = QVBoxLayout()
        layout.addWidget(grupo)
        layout.addStretch(1)
        self.setLayout(layout)
