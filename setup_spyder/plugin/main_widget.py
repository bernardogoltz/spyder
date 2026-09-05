# -*- coding: utf-8 -*-
"""Painel dockável do Claude Code."""

from __future__ import annotations

from qtpy.QtWidgets import QVBoxLayout

from spyder.api.translations import _
from spyder.api.widgets.main_widget import PluginMainWidget

from setup_spyder.plugin.api import (
    ClaudeCodeActions,
    ClaudeCodeOptionsMenuSections,
    ClaudeCodeToolbarSections,
)
from setup_spyder.plugin.terminal import ClaudePrompt, ClaudeTranscript
from setup_spyder.plugin.worker import ClaudeWorker
from setup_spyder.prereq import diagnose_prerequisites


class ClaudeCodeWidget(PluginMainWidget):

    ENABLE_SPINNER = True

    def __init__(self, name, plugin, parent=None):
        super().__init__(name, plugin, parent)
        self._worker = None
        self._busy = False
        self._pending = None
        self._current_filename = None
        self._current_selection = ""
        self._options_factory = lambda: None

        self._transcript = ClaudeTranscript(self)
        self._prompt = ClaudePrompt(self)
        self._prompt.sig_submit.connect(self.enviar)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._transcript, stretch=1)
        layout.addWidget(self._prompt, stretch=0)
        self.setLayout(layout)

    def get_title(self):
        return _("Claude Code")

    def setup(self):
        enviar = self.create_action(
            ClaudeCodeActions.Enviar,
            text=_("Enviar"),
            icon=self.create_icon("run"),
            triggered=self._enviar_do_prompt,
            register_shortcut=True,
        )
        self.create_action(
            ClaudeCodeActions.Interromper,
            text=_("Interromper"),
            icon=self.create_icon("stop"),
            triggered=self.interromper,
            register_shortcut=True,
        )
        self.create_action(
            ClaudeCodeActions.Limpar,
            text=_("Limpar"),
            icon=self.create_icon("editclear"),
            triggered=self._transcript.clear,
            register_shortcut=True,
        )
        self.create_action(
            ClaudeCodeActions.NovaSessao,
            text=_("Nova sessão"),
            icon=self.create_icon("filenew"),
            triggered=self.nova_sessao,
            register_shortcut=True,
        )
        anexar = self.create_action(
            ClaudeCodeActions.AnexarSelecao,
            text=_("Anexar arquivo/seleção atual"),
            toggled=True,
            option="anexar_selecao",
            register_shortcut=False,
        )

        toolbar = self.get_main_toolbar()
        for item in (
            enviar,
            self.get_action(ClaudeCodeActions.Interromper),
            self.get_action(ClaudeCodeActions.Limpar),
            self.get_action(ClaudeCodeActions.NovaSessao),
        ):
            self.add_item_to_toolbar(
                item,
                toolbar=toolbar,
                section=ClaudeCodeToolbarSections.Principal,
            )

        self.add_item_to_menu(
            anexar,
            menu=self.get_options_menu(),
            section=ClaudeCodeOptionsMenuSections.Opcoes,
        )
        self.update_actions()

    def update_actions(self):
        tem_texto = bool(self._transcript.toPlainText())
        self.get_action(ClaudeCodeActions.Limpar).setEnabled(tem_texto)
        self.get_action(ClaudeCodeActions.Interromper).setEnabled(self._busy)
        self.get_action(ClaudeCodeActions.Enviar).setEnabled(not self._busy)
        self._prompt.setEnabled(not self._busy)

    def update_font(self):
        self._transcript.update_theme()

    def set_editor_context(self, filename, selection):
        self._current_filename = filename
        self._current_selection = selection or ""

    def set_options_factory(self, factory):
        self._options_factory = factory

    def start_session(self):
        old = self._worker
        self._worker = None
        if old is not None:
            old.shutdown()
        avisos = diagnose_prerequisites(self.get_conf("cli_path") or "")
        for aviso in avisos:
            self._transcript.append_status(aviso)
        try:
            options = self._options_factory()
        except Exception as exc:
            self._transcript.append_error(str(exc))
            return
        worker = ClaudeWorker(options, parent=self)
        worker.sig_text.connect(self._transcript.append_text)
        worker.sig_tool.connect(self._transcript.append_tool)
        worker.sig_thinking.connect(self._transcript.append_thinking)
        worker.sig_result.connect(self._on_result)
        worker.sig_error.connect(self._on_error)
        worker.sig_busy.connect(self._on_busy)
        worker.sig_ready.connect(self._on_ready)
        self._worker = worker
        worker.start()

    def stop_session(self):
        self._pending = None
        worker = self._worker
        self._worker = None
        self._busy = False
        self.stop_spinner()
        if worker is not None:
            worker.shutdown()
        self.update_actions()

    def enviar(self, texto=None):
        if texto is None:
            texto = self._prompt.toPlainText().rstrip()
            self._prompt.clear()
        if not texto or self._busy:
            return
        prompt = self._com_contexto(texto)
        self._transcript.append_user(texto)
        self.update_actions()
        if self._worker is None or not self._worker.isRunning():
            self._pending = prompt
            self.start_session()
            return
        self._worker.submit(prompt)

    def _enviar_do_prompt(self):
        self.enviar()

    def interromper(self):
        if self._worker is not None:
            self._worker.interrupt()

    def nova_sessao(self):
        self._transcript.append_status("nova sessão")
        self.start_session()

    def _com_contexto(self, texto):
        if not self.get_conf("anexar_selecao"):
            return texto
        partes = [texto]
        if self._current_filename:
            partes.append("\n\n[arquivo atual: {}]".format(self._current_filename))
        if self._current_selection:
            partes.append(
                "\n[seleção]:\n```\n{}\n```".format(self._current_selection)
            )
        return "".join(partes)

    def _on_ready(self):
        self._transcript.append_status("sessão pronta.")
        if self._pending and self._worker is not None:
            pending, self._pending = self._pending, None
            self._worker.submit(pending)

    def _on_result(self, linha):
        self._transcript.append_result(linha)
        self.update_actions()

    def _on_error(self, mensagem):
        self._transcript.append_error(mensagem)
        self._busy = False
        self.stop_spinner()
        self.update_actions()

    def _on_busy(self, busy):
        self._busy = bool(busy)
        if self._busy:
            self.start_spinner()
        else:
            self.stop_spinner()
        self.update_actions()
