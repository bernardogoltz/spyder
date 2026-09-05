# -*- coding: utf-8 -*-
"""
Template de plugin externo SEM PAINEL para Spyder 5.x.

Use quando você só quer adicionar ações, itens de menu, botões de toolbar ou
um widget na status bar — sem ocupar espaço com um dock novo.

A diferença para o dockável: herda de SpyderPluginV2 e usa CONTAINER_CLASS
(PluginMainContainer) em vez de WIDGET_CLASS (PluginMainWidget).
"""

# =============================================================================
# container.py
# =============================================================================
from qtpy.QtCore import Signal

from spyder.api.translations import _
from spyder.api.widgets.main_container import PluginMainContainer


class MinhasAcoes:
    Formatar = 'meuplugin_formatar_action'
    AbrirPasta = 'meuplugin_abrir_pasta_action'


class MeuContainer(PluginMainContainer):
    """Guarda as ações do plugin. Não é exibido em lugar nenhum sozinho."""

    sig_pediu_formatar = Signal()

    # ---- PluginMainContainer API (os dois obrigatórios)
    # -------------------------------------------------------------------------
    def setup(self):
        self.formatar_action = self.create_action(
            MinhasAcoes.Formatar,
            text=_('Formatar arquivo atual'),
            icon=self.create_icon('run'),
            triggered=self.sig_pediu_formatar.emit,
            register_shortcut=True,   # aparece em Preferências > Atalhos
        )

        self.abrir_pasta_action = self.create_action(
            MinhasAcoes.AbrirPasta,
            text=_('Abrir pasta do projeto no explorador'),
            triggered=self._abrir_pasta,
            register_shortcut=True,
        )

    def update_actions(self):
        pass

    # ---- Privado
    # -------------------------------------------------------------------------
    def _abrir_pasta(self):
        from spyder.utils.misc import select_port  # exemplo de import local
        ...


# =============================================================================
# plugin.py
# =============================================================================
from spyder.api.plugin_registration.decorators import (
    on_plugin_available, on_plugin_teardown)
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.plugins.mainmenu.api import (
    ApplicationMenus, SourceMenuSections, ToolsMenuSections)
from spyder.plugins.toolbar.api import ApplicationToolbars, MainToolbarSections


class MeuPlugin(SpyderPluginV2):

    NAME = 'meuplugin'
    REQUIRES = [Plugins.MainMenu]
    OPTIONAL = [Plugins.Toolbar, Plugins.Editor, Plugins.StatusBar]
    CONTAINER_CLASS = MeuContainer

    CONF_SECTION = NAME
    CONF_FILE = True
    CONF_DEFAULTS = [('meuplugin', {'formatar_ao_salvar': False})]
    CONF_VERSION = '1.0.0'

    @staticmethod
    def get_name():
        return _('Meu Plugin')

    def get_description(self):
        return _('Ações extras que eu uso todo dia.')

    def get_icon(self):
        return self.create_icon('tooloptions')

    def on_initialize(self):
        self.get_container().sig_pediu_formatar.connect(self._formatar)

    # ---- Menu
    # -------------------------------------------------------------------------
    @on_plugin_available(plugin=Plugins.MainMenu)
    def on_main_menu_available(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.add_item_to_application_menu(
            self.get_container().formatar_action,
            menu_id=ApplicationMenus.Source,
            section=SourceMenuSections.Actions,
        )
        mainmenu.add_item_to_application_menu(
            self.get_container().abrir_pasta_action,
            menu_id=ApplicationMenus.Tools,
            section=ToolsMenuSections.Extras,
        )

    @on_plugin_teardown(plugin=Plugins.MainMenu)
    def on_main_menu_teardown(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.remove_item_from_application_menu(
            MinhasAcoes.Formatar, menu_id=ApplicationMenus.Source)
        mainmenu.remove_item_from_application_menu(
            MinhasAcoes.AbrirPasta, menu_id=ApplicationMenus.Tools)

    # ---- Toolbar
    # -------------------------------------------------------------------------
    @on_plugin_available(plugin=Plugins.Toolbar)
    def on_toolbar_available(self):
        toolbar = self.get_plugin(Plugins.Toolbar)
        toolbar.add_item_to_application_toolbar(
            self.get_container().formatar_action,
            toolbar_id=ApplicationToolbars.Main,
            section=MainToolbarSections.ApplicationSection,
        )

    @on_plugin_teardown(plugin=Plugins.Toolbar)
    def on_toolbar_teardown(self):
        toolbar = self.get_plugin(Plugins.Toolbar)
        toolbar.remove_item_from_application_toolbar(
            MinhasAcoes.Formatar, toolbar_id=ApplicationToolbars.Main)

    # ---- Ação em si
    # -------------------------------------------------------------------------
    def _formatar(self):
        editor = self.get_plugin(Plugins.Editor, error=False)
        if editor is None:
            return
        codeeditor = editor.get_current_editor()
        if codeeditor is None:
            return
        # ... mexer no texto ...
