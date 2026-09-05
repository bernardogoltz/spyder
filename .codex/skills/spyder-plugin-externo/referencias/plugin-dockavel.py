# -*- coding: utf-8 -*-
"""
Template de plugin externo DOCKÁVEL para Spyder 5.x.

Copie os três blocos para arquivos separados no seu pacote:
  api.py          -> bloco 1
  main_widget.py  -> bloco 2
  plugin.py       -> bloco 3
  confpage.py     -> bloco 4

Entry point (pyproject.toml):
    [project.entry-points."spyder.plugins"]
    meuplugin = "spyder_meuplugin.plugin:MeuPlugin"
"""

# =============================================================================
# BLOCO 1 — api.py : constantes de ID. Nunca use string crua no resto do código.
# =============================================================================
class MeuPluginActions:
    Rodar = 'meuplugin_rodar_action'
    Limpar = 'meuplugin_limpar_action'
    AutoRodar = 'meuplugin_auto_rodar_action'


class MeuPluginToolbarSections:
    Principal = 'meuplugin_principal_section'


class MeuPluginOptionsMenuSections:
    Opcoes = 'meuplugin_opcoes_section'


# Defaults da config própria do plugin (CONF_FILE=True).
# Formato: lista de (secao, dict_de_opcoes). A seção 'meuplugin' deve bater
# com CONF_SECTION.
CONF_DEFAULTS = [
    ('meuplugin', {
        'auto_rodar': False,
        'max_itens': 50,
    }),
]

CONF_VERSION = '1.0.0'


# =============================================================================
# BLOCO 2 — main_widget.py
# =============================================================================
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QVBoxLayout, QPlainTextEdit

from spyder.api.translations import _
from spyder.api.widgets.main_widget import PluginMainWidget


class MeuWidget(PluginMainWidget):
    """Painel do plugin."""

    # Ganha start_spinner()/stop_spinner() no canto do painel.
    ENABLE_SPINNER = True

    # O widget avisa o plugin por sinal; nunca importa outro plugin.
    sig_rodou = Signal(str)

    def __init__(self, name, plugin, parent=None):
        super().__init__(name, plugin, parent)

        self._saida = QPlainTextEdit(self)
        self._saida.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self._saida)
        self.setLayout(layout)

    # ---- PluginMainWidget API (os três obrigatórios)
    # -------------------------------------------------------------------------
    def get_title(self):
        return _('Meu Plugin')

    def setup(self):
        """Chamado uma vez. Cria ações, toolbar e options menu."""
        rodar_action = self.create_action(
            MeuPluginActions.Rodar,
            text=_('Rodar'),
            icon=self.create_icon('run'),
            triggered=self.rodar,
            # True => aparece em Preferências > Atalhos e pode ser rebindado.
            register_shortcut=True,
        )

        self.create_action(
            MeuPluginActions.Limpar,
            text=_('Limpar'),
            icon=self.create_icon('editclear'),
            triggered=self._saida.clear,
            register_shortcut=True,
        )

        # Ação-checkbox amarrada direto a uma opção de config: marcar/desmarcar
        # grava em CONF_SECTION/auto_rodar sozinho.
        auto_action = self.create_action(
            MeuPluginActions.AutoRodar,
            text=_('Rodar automaticamente'),
            toggled=True,
            option='auto_rodar',
            register_shortcut=False,
        )

        toolbar = self.get_main_toolbar()
        for item in (rodar_action, self.get_action(MeuPluginActions.Limpar)):
            self.add_item_to_toolbar(
                item, toolbar=toolbar,
                section=MeuPluginToolbarSections.Principal,
            )

        options_menu = self.get_options_menu()
        self.add_item_to_menu(
            auto_action, menu=options_menu,
            section=MeuPluginOptionsMenuSections.Opcoes,
        )

    def update_actions(self):
        """Chamado quando o estado muda. Habilita/desabilita ações."""
        self.get_action(MeuPluginActions.Limpar).setEnabled(
            bool(self._saida.toPlainText())
        )

    # ---- API pública do widget
    # -------------------------------------------------------------------------
    def rodar(self):
        self.start_spinner()
        try:
            texto = 'rodou'
            self._saida.appendPlainText(texto)
            self.sig_rodou.emit(texto)
        finally:
            self.stop_spinner()
        self.update_actions()


# =============================================================================
# BLOCO 3 — plugin.py
# =============================================================================
from spyder.api.config.decorators import on_conf_change
from spyder.api.plugin_registration.decorators import (
    on_plugin_available, on_plugin_teardown)
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections


class MeuPlugin(SpyderDockablePlugin):

    NAME = 'meuplugin'                  # == nome do entry point
    REQUIRES = [Plugins.Preferences]
    OPTIONAL = [Plugins.MainMenu, Plugins.Editor]
    TABIFY = [Plugins.Help]
    WIDGET_CLASS = MeuWidget

    CONF_SECTION = NAME
    CONF_FILE = True
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION
    CONF_WIDGET_CLASS = None            # troque por MeuConfPage (bloco 4)

    CAN_BE_DISABLED = True

    # ---- SpyderDockablePlugin API
    # -------------------------------------------------------------------------
    @staticmethod
    def get_name():
        return _('Meu Plugin')

    def get_description(self):
        return _('Faz aquilo que eu preciso.')

    def get_icon(self):
        return self.create_icon('genericfile')

    def on_initialize(self):
        # Só coisas próprias. Outros plugins ainda podem não existir.
        self.get_widget().sig_rodou.connect(self._registrar)

    # ---- Integração com outros plugins (sempre em pares)
    # -------------------------------------------------------------------------
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
            self.get_widget().get_action(MeuPluginActions.Rodar),
            menu_id=ApplicationMenus.Tools,
            section=ToolsMenuSections.Extras,
        )

    @on_plugin_teardown(plugin=Plugins.MainMenu)
    def on_main_menu_teardown(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.remove_item_from_application_menu(
            MeuPluginActions.Rodar,
            menu_id=ApplicationMenus.Tools,
        )

    # ---- Reagir a mudança de config
    # -------------------------------------------------------------------------
    @on_conf_change(option='max_itens')
    def _on_max_itens(self, value):
        self.get_widget().update_actions()

    # ---- Trabalho pesado só depois da janela aparecer
    # -------------------------------------------------------------------------
    def on_mainwindow_visible(self):
        pass

    # ---- Privado
    # -------------------------------------------------------------------------
    def _registrar(self, texto):
        # Exemplo de uso de plugin opcional: só age se o Editor existir.
        editor = self.get_plugin(Plugins.Editor, error=False)
        if editor is not None:
            pass


# =============================================================================
# BLOCO 4 — confpage.py : a página em Preferências
# =============================================================================
from qtpy.QtWidgets import QGroupBox, QVBoxLayout

from spyder.api.preferences import PluginConfigPage


class MeuConfPage(PluginConfigPage):

    def setup_page(self):
        grupo = QGroupBox(_('Comportamento'))

        # Estes helpers já leem/gravam na CONF_SECTION do plugin.
        auto = self.create_checkbox(
            _('Rodar automaticamente'), 'auto_rodar')
        maxi = self.create_spinbox(
            _('Máximo de itens:'), '', 'max_itens',
            min_=1, max_=1000, step=1)

        layout_grupo = QVBoxLayout()
        layout_grupo.addWidget(auto)
        layout_grupo.addWidget(maxi)
        grupo.setLayout(layout_grupo)

        layout = QVBoxLayout()
        layout.addWidget(grupo)
        layout.addStretch(1)
        self.setLayout(layout)
