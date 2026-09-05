# -*- coding: utf-8 -*-
"""Transcript + prompt com cara de terminal."""

from __future__ import annotations

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QColor, QFont, QKeyEvent, QTextCharFormat, QTextCursor
from qtpy.QtWidgets import QPlainTextEdit

from spyder.config.gui import get_font
from spyder.utils.palette import SpyderPalette

from setup_spyder.render import format_user_line


class ClaudeTranscript(QPlainTextEdit):
    """Read-only, fonte do editor, cores da paleta do Spyder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._apply_font()
        self._apply_style()

    def _apply_font(self):
        try:
            self.setFont(get_font())
        except Exception:
            self.setFont(QFont("Consolas", 10))

    def _apply_style(self):
        self.setStyleSheet(
            "QPlainTextEdit {{ background: transparent; color: {}; "
            "border: none; }}".format(SpyderPalette.ICON_1)
        )

    def update_theme(self):
        self._apply_font()
        self._apply_style()

    def append_line(self, text, color=None, bold=False):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color or SpyderPalette.ICON_1))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        cursor.setCharFormat(fmt)
        cursor.insertText(text.rstrip() + "\n")
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_user(self, text):
        self.append_line(
            format_user_line(text),
            color=SpyderPalette.COLOR_HIGHLIGHT_4,
            bold=True,
        )

    def append_text(self, text):
        self.append_line(text, color=SpyderPalette.ICON_1)

    def append_tool(self, text):
        self.append_line(text, color=SpyderPalette.GROUP_4)

    def append_thinking(self):
        self.append_line("⋯ pensamento", color=SpyderPalette.ICON_6)

    def append_result(self, text):
        self.append_line(text, color=SpyderPalette.COLOR_SUCCESS_1)

    def append_error(self, text):
        self.append_line(text, color=SpyderPalette.COLOR_ERROR_1, bold=True)

    def append_status(self, text):
        self.append_line(text, color=SpyderPalette.ICON_6)


class ClaudePrompt(QPlainTextEdit):
    """Enter envia, Shift+Enter quebra linha, ↑/↓ navegam o histórico."""

    sig_submit = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabChangesFocus(True)
        self.setMaximumHeight(90)
        self.setPlaceholderText("pergunte ao Claude…  Enter envia, Shift+Enter quebra linha")
        self._history = []
        self._index = None
        self._draft = ""
        try:
            self.setFont(get_font())
        except Exception:
            pass

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        if key in (Qt.Key_Return, Qt.Key_Enter) and not (mods & Qt.ShiftModifier):
            texto = self.toPlainText().rstrip()
            if texto:
                self._history.append(texto)
                self._index = None
                self._draft = ""
                self.clear()
                self.sig_submit.emit(texto)
            event.accept()
            return
        if key == Qt.Key_Up and not (mods & Qt.ShiftModifier):
            if self._history and self.textCursor().blockNumber() == 0:
                self._hist(-1)
                event.accept()
                return
        if key == Qt.Key_Down and not (mods & Qt.ShiftModifier):
            last = self.document().blockCount() - 1
            if self._history and self.textCursor().blockNumber() == last:
                self._hist(1)
                event.accept()
                return
        super().keyPressEvent(event)

    def _hist(self, delta):
        if not self._history:
            return
        if self._index is None:
            self._draft = self.toPlainText()
            self._index = len(self._history)
        nxt = self._index + delta
        if nxt < 0:
            nxt = 0
        if nxt > len(self._history):
            nxt = len(self._history)
        self._index = nxt
        if nxt == len(self._history):
            self.setPlainText(self._draft)
        else:
            self.setPlainText(self._history[nxt])
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
