# -*- coding: utf-8 -*-
"""SpyderDockablePlugin do Claude Code."""

from __future__ import annotations

import os

from spyder.api.plugin_registration.decorators import (
    on_plugin_available,
    on_plugin_teardown,
)
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.translations import _
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections

from setup_spyder.plugin.api import (
    CONF_DEFAULTS,
    CONF_VERSION,
    ClaudeCodeActions,
)
from setup_spyder.plugin.confpage import ClaudeCodeConfPage
from setup_spyder.plugin.main_widget import ClaudeCodeWidget


class ClaudeCodePlugin(SpyderDockablePlugin):

    NAME = "claude_code"
    REQUIRES = [Plugins.Preferences]
    OPTIONAL = [Plugins.Editor, Plugins.MainMenu, Plugins.Projects]
    TABIFY = [Plugins.IPythonConsole]
    WIDGET_CLASS = ClaudeCodeWidget
    CONF_SECTION = NAME
    CONF_FILE = True
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION
    CONF_WIDGET_CLASS = ClaudeCodeConfPage
    CAN_BE_DISABLED = True

    @staticmethod
    def get_name():
        return _("Claude Code")

    def get_description(self):
        return _("Painel do Claude Code no Spyder, com cara de terminal.")

    def get_icon(self):
        return self.create_icon("ipython_console")

    @staticmethod
    def check_compatibility():
        import sys

        if sys.version_info < (3, 10):
            return False, _("Claude Code exige Python 3.10 ou superior.")
        return True, ""

    def on_initialize(self):
        widget = self.get_widget()
        widget.set_options_factory(self._agent_options)

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        self.get_plugin(Plugins.Preferences).register_plugin_preferences(self)

    @on_plugin_teardown(plugin=Plugins.Preferences)
    def on_preferences_teardown(self):
        self.get_plugin(Plugins.Preferences).deregister_plugin_preferences(self)

    @on_plugin_available(plugin=Plugins.MainMenu)
    def on_main_menu_available(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.add_item_to_application_menu(
            self.get_widget().get_action(ClaudeCodeActions.Enviar),
            menu_id=ApplicationMenus.Tools,
            section=ToolsMenuSections.Extras,
        )

    @on_plugin_teardown(plugin=Plugins.MainMenu)
    def on_main_menu_teardown(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.remove_item_from_application_menu(
            ClaudeCodeActions.Enviar,
            menu_id=ApplicationMenus.Tools,
        )

    @on_plugin_available(plugin=Plugins.Editor)
    def on_editor_available(self):
        editor = self.get_plugin(Plugins.Editor)
        editor.sig_editor_focus_changed.connect(self._atualizar_contexto)
        self._atualizar_contexto()

    @on_plugin_teardown(plugin=Plugins.Editor)
    def on_editor_teardown(self):
        editor = self.get_plugin(Plugins.Editor)
        editor.sig_editor_focus_changed.disconnect(self._atualizar_contexto)

    def on_mainwindow_visible(self):
        self.get_widget().start_session()

    def on_close(self, cancelable=False):
        self.get_widget().stop_session()

    def update_font(self):
        self.get_widget().update_font()

    def _atualizar_contexto(self):
        editor = self.get_plugin(Plugins.Editor, error=False)
        filename = None
        selection = ""
        if editor is not None:
            filename = editor.get_current_filename()
            widget = editor.get_current_editor()
            if widget is not None and hasattr(widget, "get_selected_text"):
                selection = widget.get_selected_text() or ""
        self.get_widget().set_editor_context(filename, selection)

    def _cwd(self):
        projects = self.get_plugin(Plugins.Projects, error=False)
        if projects is not None:
            path = projects.get_active_project_path()
            if path:
                return path
        return os.getcwd()

    def _agent_options(self):
        from claude_agent_sdk import ClaudeAgentOptions

        cli_path = (self.get_conf("cli_path") or "").strip() or None
        add_dirs = [
            item.strip()
            for item in (self.get_conf("add_dirs") or "").split(";")
            if item.strip()
        ]
        effort = self.get_conf("effort") or None
        kwargs = dict(
            cwd=self._cwd(),
            model=self.get_conf("model") or "claude-opus-5",
            permission_mode=self.get_conf("permission_mode") or "acceptEdits",
            setting_sources=["user", "project", "local"],
            tools={"type": "preset", "preset": "claude_code"},
        )
        if cli_path:
            kwargs["cli_path"] = cli_path
        if add_dirs:
            kwargs["add_dirs"] = add_dirs
        if effort:
            kwargs["effort"] = effort
        return ClaudeAgentOptions(**kwargs)
