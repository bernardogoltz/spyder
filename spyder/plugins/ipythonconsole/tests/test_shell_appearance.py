# -*- coding: utf-8 -*-
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Check console appearance without starting a kernel."""

from unittest.mock import Mock

import pytest
from qtpy.QtGui import QColor, QFont, QTextCursor

from spyder.config.gui import get_color_scheme
from spyder.plugins.ipythonconsole.utils.style import create_qss_style
from spyder.plugins.ipythonconsole.widgets.shell import ShellWidget


@pytest.fixture
def shell(qtbot):
    widget = ShellWidget(
        ipyclient=Mock(), additional_options={}, interpreter_versions={},
        is_external_kernel=False, is_spyder_kernel=False, handlers={},
        syntax_style='spyder/dark',
        style_sheet=create_qss_style('spyder/dark')[0])
    qtbot.addWidget(widget)
    widget.resize(600, 320)
    return widget


def test_font_change_preserves_console_content(shell):
    """Font-scaled margins must not replace text or disturb selection."""
    control = shell._control
    control.setPlainText('In [1]: total = 42\nOut[1]: 42')
    shell._page_control.setPlainText('Help on total')
    cursor = control.textCursor()
    cursor.setPosition(8)
    cursor.setPosition(18, QTextCursor.KeepAnchor)
    control.setTextCursor(cursor)
    text = control.toPlainText()
    selection = cursor.selectedText()

    shell.font = QFont('Monospace', 10)
    margin = control.document().documentMargin()
    shell.font = QFont('Monospace', 20)

    assert control.document().documentMargin() > margin
    assert (shell._page_control.document().documentMargin()
            == control.document().documentMargin())
    assert control.toPlainText() == text
    assert control.textCursor().selectedText() == selection
    assert shell._page_control.toPlainText() == 'Help on total'


@pytest.mark.parametrize('scheme_name', ['spyder', 'spyder/dark'])
def test_prompt_colors_follow_syntax_theme(shell, scheme_name):
    """Qt must render input/output prompts in the selected theme colors."""
    shell.style_sheet = create_qss_style(scheme_name)[0]
    shell._style_sheet_changed()
    shell._append_html(
        '<span class="in-prompt">In [1]: </span>total = 42<br>'
        '<span class="out-prompt">Out[1]: </span>42', before_prompt=False)
    document = shell._control.document()
    scheme = get_color_scheme(scheme_name)
    for prompt, token in [('In [1]', 'keyword'), ('Out[1]', 'number')]:
        cursor = document.find(prompt)
        assert not cursor.isNull()
        assert cursor.charFormat().foreground().color() == QColor(
            scheme[token][0])
