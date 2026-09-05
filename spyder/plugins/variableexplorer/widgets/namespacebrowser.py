# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Namespace browser widget.

This is the main widget used in the Variable Explorer plugin
"""

# Standard library imports
import os
import os.path as osp

# Third library imports
from qtpy import PYQT5
from qtpy.compat import getopenfilenames, getsavefilename
from qtpy.QtCore import QEvent, Qt, Signal, Slot
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import (QAbstractItemView, QApplication, QFrame,
                            QInputDialog, QLabel, QMessageBox, QVBoxLayout,
                            QWidget)
from spyder_kernels.utils.iofuncs import iofunctions
from spyder_kernels.utils.misc import fix_reference_name
from spyder_kernels.utils.nsview import REMOTE_SETTINGS

# Local imports
from spyder.api.translations import _
from spyder.api.widgets.mixins import SpyderWidgetMixin
from spyder.widgets.collectionseditor import RemoteCollectionsEditorTableView
from spyder.plugins.variableexplorer.widgets.importwizard import ImportWizard
from spyder.utils import encoding
from spyder.utils.misc import getcwd_or_home, remove_backslashes
from spyder.widgets.helperwidgets import FinderLineEdit


# Constants
VALID_VARIABLE_CHARS = r"[^\w+*=¡!¿?'\"#$%&()/<>\-\[\]{}^`´;,|¬]*\w"


class NamespaceTableView(RemoteCollectionsEditorTableView):
    """Variable table with comfortable spacing and useful empty states."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.NoFrame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._update_row_height()

        # Keep the viewport interactive for paste, context menus and drops.
        self.empty_message = QLabel(self.viewport())
        self.empty_message.setAlignment(Qt.AlignCenter)
        self.empty_message.setWordWrap(True)
        self.empty_message.setTextFormat(Qt.PlainText)
        self.empty_message.setAttribute(Qt.WA_TransparentForMouseEvents)
        empty_layout = QVBoxLayout(self.viewport())
        empty_layout.setContentsMargins(24, 24, 24, 24)
        empty_layout.addWidget(self.empty_message)

        for signal in (self.proxy_model.modelReset,
                       self.proxy_model.rowsInserted,
                       self.proxy_model.rowsRemoved,
                       self.proxy_model.layoutChanged):
            signal.connect(self._update_empty_message)
        self._update_empty_message()

    def _update_row_height(self):
        """Use a fixed default height without measuring every variable."""
        self.verticalHeader().setDefaultSectionSize(
            max(28, self.fontMetrics().height() + 12))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:
            self._update_row_height()

    def _update_empty_message(self, *args):
        """Distinguish an empty namespace from a search with no matches."""
        empty = self.proxy_model.rowCount() == 0
        if empty:
            if self.source_model.total_rows:
                message = _("No matching variables.\n"
                            "Try another name or type, or clear the search.")
            else:
                message = _("No variables to show.\n"
                            "Run code, import data, or review the filters.")
            self.empty_message.setText(message)
        self.empty_message.setVisible(empty)


class NamespaceBrowser(QWidget, SpyderWidgetMixin):
    """
    Namespace browser (global variables explorer widget).
    """
    # This is necessary to test the widget separately from its plugin
    CONF_SECTION = 'variable_explorer'

    # Signals
    sig_free_memory_requested = Signal()
    sig_start_spinner_requested = Signal()
    sig_stop_spinner_requested = Signal()
    sig_hide_finder_requested = Signal()

    def __init__(self, parent):
        if PYQT5:
            super().__init__(parent=parent, class_parent=parent)
        else:
            QWidget.__init__(self, parent)
            SpyderWidgetMixin.__init__(self, class_parent=parent)

        # Attributes
        self.filename = None
        self.text_finder = None
        self.last_find = ''
        self.finder_is_visible = False

        # Widgets
        self.editor = None
        self.shellwidget = None

    def setup(self):
        """
        Setup the namespace browser with provided options.
        """
        assert self.shellwidget is not None

        if self.editor is not None:
            self.shellwidget.set_namespace_view_settings()
            self.refresh_table()
        else:
            # Widgets
            self.editor = NamespaceTableView(
                self,
                data=None,
                shellwidget=self.shellwidget,
                create_menu=False,
            )

            # Signals
            self.editor.sig_files_dropped.connect(self.import_data)
            self.editor.sig_free_memory_requested.connect(
                self.sig_free_memory_requested)
            self.editor.sig_editor_creation_started.connect(
                self.sig_start_spinner_requested)
            self.editor.sig_editor_shown.connect(
                self.sig_stop_spinner_requested)

            # Layout
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.editor)
            self.setLayout(layout)

    def get_view_settings(self):
        """Return dict editor view settings"""
        settings = {}
        for name in REMOTE_SETTINGS:
            settings[name] = self.get_conf(name)

        return settings

    def set_shellwidget(self, shellwidget):
        """Bind shellwidget instance to namespace browser"""
        self.shellwidget = shellwidget
        shellwidget.set_namespacebrowser(self)

    def set_text_finder(self, text_finder):
        """Bind NamespaceBrowsersFinder to namespace browser."""
        self.text_finder = text_finder
        self.editor.finder = text_finder
        if self.finder_is_visible:
            if text_finder.text() == self.last_find:
                # Restoring identical text emits no textChanged signal. The
                # inactive namespace may have received a paginated refresh.
                if self.last_find:
                    text_finder.load_all_variables()
                self.editor.set_regex()
            else:
                text_finder.setText(self.last_find)

        return self.finder_is_visible

    def save_finder_state(self, last_find, finder_visibility):
        """Save last finder/search text input and finder visibility."""
        if finder_visibility:
            self.last_find = last_find
        self.finder_is_visible = finder_visibility

    def refresh_table(self):
        """Refresh variable table."""
        self.shellwidget.refresh_namespacebrowser()
        try:
            self.editor.resizeRowToContents()
        except TypeError:
            pass

    def process_remote_view(self, remote_view):
        """Process remote view"""
        # To load all variables when a new filtering search is
        # started.
        self.text_finder.load_all = False

        if remote_view is not None:
            self.set_data(remote_view)

    def set_var_properties(self, properties):
        """Set properties of variables"""
        if properties is not None:
            self.editor.var_properties = properties

    def set_data(self, data):
        """Set data."""
        if data != self.editor.source_model.get_data():
            self.editor.set_data(data)
            if (self.text_finder is not None
                    and self.text_finder._parent is self.editor
                    and self.text_finder.text()):
                # A kernel refresh resets pagination; keep the active search
                # complete even when its matches fall beyond the first page.
                self.editor.source_model.load_all()
                self.editor.set_regex()
            self.editor.adjust_columns()

    @Slot(list)
    def import_data(self, filenames=None):
        """Import data from text file."""
        title = _("Import data")
        if filenames is None:
            if self.filename is None:
                basedir = getcwd_or_home()
            else:
                basedir = osp.dirname(self.filename)
            filenames, _selfilter = getopenfilenames(self, title, basedir,
                                                     iofunctions.load_filters)
            if not filenames:
                return
        elif isinstance(filenames, str):
            filenames = [filenames]

        for filename in filenames:
            self.filename = str(filename)
            if os.name == "nt":
                self.filename = remove_backslashes(self.filename)
            extension = osp.splitext(self.filename)[1].lower()

            if extension == '.spydata':
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                answer = QMessageBox.warning(
                    self,
                    title,
                    _("<b>Warning: %s files can contain malicious code!</b>"
                      "<br><br>"
                      "Do not continue unless this file is from a trusted "
                      "source. Would you like to import it "
                      "anyway?") % extension,
                    buttons
                )

                if answer == QMessageBox.Cancel:
                    return
            if extension not in iofunctions.load_funcs:
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                answer = QMessageBox.question(
                    self,
                    title,
                    _("<b>Unsupported file extension '%s'</b>"
                      "<br><br>"
                      "Would you like to import it anyway by selecting a "
                      "known file format?") % extension,
                    buttons
                )
                if answer == QMessageBox.Cancel:
                    return
                formats = list(iofunctions.load_extensions.keys())
                item, ok = QInputDialog.getItem(self, title,
                                                _('Open file as:'),
                                                formats, 0, False)
                if ok:
                    extension = iofunctions.load_extensions[str(item)]
                else:
                    return

            load_func = iofunctions.load_funcs[extension]
                
            # 'import_wizard' (self.setup_io)
            if isinstance(load_func, str):
                # Import data with import wizard
                error_message = None
                try:
                    text, _encoding = encoding.read(self.filename)
                    base_name = osp.basename(self.filename)
                    editor = ImportWizard(self, text, title=base_name,
                                  varname=fix_reference_name(base_name))
                    if editor.exec_():
                        var_name, clip_data = editor.get_data()
                        self.editor.new_value(var_name, clip_data)
                except Exception as error:
                    error_message = str(error)
            else:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                QApplication.processEvents()
                error_message = self.shellwidget.load_data(self.filename,
                                                           extension)
                QApplication.restoreOverrideCursor()
                QApplication.processEvents()
    
            if error_message is not None:
                QMessageBox.critical(self, title,
                                     _("<b>Unable to load '%s'</b>"
                                       "<br><br>"
                                       "The error message was:<br>%s"
                                       ) % (self.filename, error_message))
            self.refresh_table()

    def reset_namespace(self):
        warning = self.get_conf(
            section='ipython_console',
            option='show_reset_namespace_warning'
        )
        self.shellwidget.reset_namespace(warning=warning, message=True)
        self.editor.automatic_column_width = True

    def save_data(self):
        """Save data"""
        filename = self.filename
        if filename is None:
            filename = getcwd_or_home()
        extension = osp.splitext(filename)[1].lower()
        if not extension:
            # Needed to prevent trying to save a data file without extension
            # See spyder-ide/spyder#7196
            filename = filename + '.spydata'
        filename, _selfilter = getsavefilename(self, _("Save data"),
                                               filename,
                                               iofunctions.save_filters)
        if filename:
            self.filename = filename
        else:
            return False

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        error_message = self.shellwidget.save_namespace(self.filename)

        QApplication.restoreOverrideCursor()
        QApplication.processEvents()
        if error_message is not None:
            if 'Some objects could not be saved:' in error_message:
                save_data_message = (
                    _("<b>Some objects could not be saved:</b>")
                    + "<br><br><code>{obj_list}</code>".format(
                        obj_list=error_message.split(': ')[1]))
            else:
                save_data_message = _(
                    "<b>Unable to save current workspace</b>"
                    "<br><br>"
                    "The error message was:<br>") + error_message

            QMessageBox.critical(self, _("Save data"), save_data_message)


class NamespacesBrowserFinder(FinderLineEdit):
    """Textbox for filtering listed variables in the table."""
    # To load all variables when filtering.
    load_all = False

    def __init__(self, parent, callback=None, main=None,
                 regex_base=VALID_VARIABLE_CHARS):
        super().__init__(parent, main=main, regex_base=regex_base)
        self.setPlaceholderText(_("Filter variables by name or type"))
        self.setAccessibleName(_("Filter variables"))
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(30)
        self.setTextMargins(4, 0, 4, 0)
        self.update_parent(parent, callback=callback, main=main)

    def update_parent(self, parent, callback=None, main=None):
        self._parent = parent
        self.main = main
        self.load_all = False
        try:
            self.textChanged.disconnect()
        except TypeError:
            pass
        # Also covers paste, the clear button and restoring a saved search.
        self.textChanged.connect(self._prepare_filter)
        if callback:
            self.textChanged.connect(callback)

    def _prepare_filter(self, text):
        if text:
            self.load_all_variables()

    def load_all_variables(self):
        """Load all variables to correctly filter them."""
        if not self.load_all:
            self._parent.source_model.load_all()
        self.load_all = True

    def keyPressEvent(self, event):
        """Qt and FilterLineEdit Override."""
        key = event.key()
        if key in [Qt.Key_Up]:
            self.load_all_variables()
            self._parent.previous_row()
        elif key in [Qt.Key_Down]:
            self.load_all_variables()
            self._parent.next_row()
        elif key in [Qt.Key_Escape]:
            self.main.sig_hide_finder_requested.emit()
        elif key in [Qt.Key_Enter, Qt.Key_Return]:
            # TODO: Check if an editor needs to be shown
            pass
        else:
            super(NamespacesBrowserFinder, self).keyPressEvent(event)
