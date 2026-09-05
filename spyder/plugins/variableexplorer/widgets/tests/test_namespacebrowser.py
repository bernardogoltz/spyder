# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""
Tests for namespacebrowser.py
"""

# Standard library imports
import string
from unittest.mock import Mock

# Third party imports
from flaky import flaky
import pytest
from qtpy.QtCore import Qt, QPoint, QModelIndex

# Local imports
from spyder.plugins.variableexplorer.widgets.namespacebrowser import (
    NamespaceBrowser, NamespacesBrowserFinder, VALID_VARIABLE_CHARS)
from spyder.widgets.collectionseditor import ROWS_TO_LOAD
from spyder.widgets.tests.test_collectioneditor import data, data_table


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def namespacebrowser(qtbot):
    browser = NamespaceBrowser(None)
    browser.set_shellwidget(Mock())
    browser.setup()
    browser.resize(640, 480)
    browser.show()
    qtbot.addWidget(browser)
    return browser


# =============================================================================
# ---- Tests
# =============================================================================
@flaky(max_runs=5)
def test_automatic_column_width(namespacebrowser):
    browser = namespacebrowser

    col_width = [browser.editor.columnWidth(i) for i in range(4)]
    browser.set_data({'a_variable':
        {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
         'numpy_type': 'Unknown'}})
    new_col_width = [browser.editor.columnWidth(i) for i in range(4)]
    assert browser.editor.automatic_column_width
    assert col_width != new_col_width  # Automatic col width is on
    browser.editor.horizontalHeader()._handle_section_is_pressed = True
    browser.editor.setColumnWidth(0, 100)  # Simulate user changing col width
    assert browser.editor.automatic_column_width == False
    browser.set_data({'a_lengthy_variable_name_which_should_change_width':
        {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
         'numpy_type': 'Unknown'}})
    assert browser.editor.columnWidth(0) == 100  # Automatic col width is off


def test_sort_by_column(namespacebrowser, qtbot):
    """
    Test that clicking the header view the namespacebrowser is sorted.
    Regression test for spyder-ide/spyder#9835 .
    """
    browser = namespacebrowser

    browser.set_data(
        {'a_variable':
            {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
             'numpy_type': 'Unknown'},
         'b_variable':
            {'type': 'int', 'size': 1, 'view': '2', 'python_type': 'int',
             'numpy_type': 'Unknown'}}
    )

    header = browser.editor.horizontalHeader()

    # Check header is clickable
    assert header.sectionsClickable()

    model = browser.editor.model

    # Base check of the model
    assert model.rowCount() == 2
    assert model.columnCount() == 5
    assert data_table(model, 2, 4) == [['a_variable', 'b_variable'],
                                       ['int', 'int'],
                                       [1, 1],
                                       ['1', '2']]

    with qtbot.waitSignal(header.sectionClicked):
        browser.show()
        qtbot.mouseClick(header.viewport(), Qt.LeftButton, pos=QPoint(1, 1))

    # Check sort effect
    assert data_table(model, 2, 4) == [['b_variable', 'a_variable'],
                                       ['int', 'int'],
                                       [1, 1],
                                       ['2', '1']]


def test_keys_sorted_and_sort_with_large_rows(namespacebrowser, qtbot):
    """
    Test that keys are sorted and sorting works as expected when
    there's a large number of rows.

    This is a regression test for issue spyder-ide/spyder#10702
    """
    browser = namespacebrowser

    # Create variables.
    variables = {}
    variables['i'] = (
        {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
         'numpy_type': 'Unknown'}
    )

    for i in range(100):
        if i < 10:
            var = 'd_0' + str(i)
        else:
            var = 'd_' + str(i)
        variables[var] = (
            {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
             'numpy_type': 'Unknown'}
        )

    # Set data
    browser.set_data(variables)

    # Assert we loaded the expected amount of data and that we can fetch
    # more.
    model = browser.editor.model
    assert model.rowCount() == ROWS_TO_LOAD
    assert model.canFetchMore(QModelIndex())

    # Assert keys are sorted
    assert data(model, 49, 0) == 'd_49'

    # Sort
    header = browser.editor.horizontalHeader()
    with qtbot.waitSignal(header.sectionClicked):
        qtbot.mouseClick(header.viewport(), Qt.LeftButton, pos=QPoint(1, 1))

    # Assert we loaded all data before performing the sort.
    assert data(model, 0, 0) == 'i'


@pytest.mark.parametrize('programmatic', [False, True])
def test_filtering_with_large_rows(namespacebrowser, qtbot, programmatic):
    """
    Test that filtering works when there's a large number of rows.
    """
    browser = namespacebrowser

    text_finder = NamespacesBrowserFinder(
        browser.editor,
        callback=browser .editor.set_regex,
        main=browser,
        regex_base=VALID_VARIABLE_CHARS)
    browser.set_text_finder(text_finder)

    # Create data
    variables = {}
    for i in range(200):
        letter = string.ascii_lowercase[i // 10]
        var = letter + str(i)
        variables[var] = (
            {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
             'numpy_type': 'Unknown'}
        )

    # Set data
    browser.set_data(variables)

    # Assert we loaded the expected amount of data and that we can fetch
    # more data.
    model = browser.editor.model
    assert model.rowCount() == ROWS_TO_LOAD
    assert model.canFetchMore(QModelIndex())
    assert data(model, 49, 0) == 'e49'

    # Assert we can filter variables not loaded yet.
    if programmatic:
        # Restoring a search and pasting from the context menu bypass keyPress.
        text_finder.setText("t19")
    else:
        qtbot.keyClicks(text_finder, "t19")
    assert model.rowCount() == 10

    # Assert all variables effectively start with 't19'.
    for i in range(10):
        assert data(model, i, 0) == 't19{}'.format(i)

    # A refresh must preserve matches outside the first loaded page.
    refreshed_variables = variables.copy()
    # Replace a record, since the editor still references the original data.
    refreshed_variables['t199'] = dict(
        refreshed_variables['t199'], view='2')
    browser.process_remote_view(refreshed_variables)
    assert model.rowCount() == 10

    # Reset text_finder widget.
    text_finder.setText('')

    # Create a new variable that starts with a different letter than
    # the rest.
    new_variables = variables.copy()
    new_variables['z'] = (
        {'type': 'int', 'size': 1, 'view': '1', 'python_type': 'int',
         'numpy_type': 'Unknown'}
    )

    # Emulate the process of loading those variables after the
    # namespace view is sent from the kernel.
    browser.process_remote_view(new_variables)

    # Assert that can find 'z' among the declared variables.
    qtbot.keyClicks(text_finder, "z")
    assert model.rowCount() == 1


def test_same_search_after_inactive_namespace_refresh(namespacebrowser, qtbot):
    """Switching consoles reapplies an unchanged search after pagination."""
    first = namespacebrowser
    second = NamespaceBrowser(None)
    second.set_shellwidget(Mock())
    second.setup()
    qtbot.addWidget(second)

    variables = {
        'v{:03d}'.format(i): {
            'type': 'int', 'size': 1, 'view': str(i),
            'python_type': 'int', 'numpy_type': 'Unknown'}
        for i in range(200)
    }
    first.set_data(variables)
    second.set_data(variables)
    finder = NamespacesBrowserFinder(
        first.editor, callback=first.editor.set_regex, main=first)
    first.set_text_finder(finder)
    finder.setText('v19')
    first.save_finder_state('v19', True)
    assert first.editor.model.rowCount() == 20

    finder.update_parent(
        second.editor, callback=second.editor.set_regex, main=second)
    second.set_text_finder(finder)
    finder.clear()
    finder.setText('v19')
    second.save_finder_state('v19', True)
    assert second.editor.model.rowCount() == 20

    refreshed_variables = variables.copy()
    refreshed_variables['v199'] = dict(variables['v199'], view='changed')
    first.process_remote_view(refreshed_variables)
    assert first.editor.source_model.canFetchMore(QModelIndex())

    # The shared line edit already contains the restored text: Qt emits no
    # textChanged signal, but the first table must still reload its matches.
    finder.update_parent(
        first.editor, callback=first.editor.set_regex, main=first)
    first.set_text_finder(finder)
    assert first.editor.model.rowCount() == 20
    assert not first.editor.source_model.canFetchMore(QModelIndex())
    assert not first.editor.empty_message.isVisible()


def test_empty_namespace_and_search_message(namespacebrowser):
    """Keep the table usable while explaining empty search results."""
    browser = namespacebrowser
    editor = browser.editor
    message = editor.empty_message
    assert message.isVisible()
    empty_text = message.text()
    assert message.testAttribute(Qt.WA_TransparentForMouseEvents)

    finder = NamespacesBrowserFinder(
        editor, callback=editor.set_regex, main=browser)
    browser.set_text_finder(finder)
    browser.set_data({'answer': {
        'type': 'int', 'size': 1, 'view': '42', 'python_type': 'int',
        'numpy_type': 'Unknown'}})
    assert not message.isVisible()

    finder.setText('missing')
    assert message.isVisible()
    assert message.text() != empty_text
    finder.clear()
    assert editor.model.rowCount() == 1
    assert not message.isVisible()

    browser.set_data({})
    assert message.isVisible()
    assert message.text() == empty_text


def test_cleared_search_state_is_saved(namespacebrowser):
    """A cleared search should not reappear when switching consoles."""
    browser = namespacebrowser
    browser.save_finder_state('answer', True)
    browser.save_finder_state('', True)
    assert browser.last_find == ''


if __name__ == "__main__":
    pytest.main()
