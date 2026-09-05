# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Spyder font variables
"""

import os
import os.path as osp
import sys

from spyder.config.utils import is_ubuntu


#==============================================================================
# Main fonts
#==============================================================================
# Rich text fonts
SANS_SERIF = ['Sans Serif', 'DejaVu Sans', 'Bitstream Vera Sans',
              'Bitstream Charter', 'Lucida Grande', 'MS Shell Dlg 2',
              'Calibri', 'Verdana', 'Geneva', 'Lucid', 'Arial',
              'Helvetica', 'Avant Garde', 'Times', 'sans-serif']

# Plan text fonts
MONOSPACE = ['Monospace', 'DejaVu Sans Mono', 'Consolas',
             'Bitstream Vera Sans Mono', 'Andale Mono', 'Liberation Mono',
             'Courier New', 'Courier', 'monospace', 'Fixed', 'Terminal']


#==============================================================================
# Adjust font size per OS
#==============================================================================
if sys.platform == 'darwin':
    MONOSPACE = ['Menlo'] + MONOSPACE
    BIG = MEDIUM = SMALL = 11
elif os.name == 'nt':
    BIG = MEDIUM = 10
    SMALL = 9
elif is_ubuntu():
    SANS_SERIF = ['Ubuntu'] + SANS_SERIF
    MONOSPACE = ['Ubuntu Mono'] + MONOSPACE
    BIG = MEDIUM = 11
    SMALL = 10
else:
    BIG = 10
    MEDIUM = SMALL = 9

#==============================================================================
# Fonts bundled with Spyder
#==============================================================================
# Directory where the font files we ship live
BUNDLED_FONTS_PATH = osp.join(
    osp.dirname(osp.realpath(__file__)), '..', 'fonts', 'fonts')

# Plain text font we ship, so that it's available without being installed
# system-wide
JETBRAINS_MONO = 'JetBrains Mono'

# Prefer our bundled font over the ones provided by the OS
MONOSPACE = [JETBRAINS_MONO] + MONOSPACE

_bundled_fonts_loaded = False


def get_bundled_font_path(*names):
    """Return the path of a font file shipped in spyder/fonts/fonts."""
    return osp.join(BUNDLED_FONTS_PATH, *names)


def load_bundled_fonts():
    """
    Register the fonts we ship in the application font database.

    This makes them available to `get_family` even when they are not
    installed system-wide. A QApplication needs to exist for this to work,
    which is why it's called from `spyder.utils.qthelpers.qapplication`.
    """
    global _bundled_fonts_loaded
    if _bundled_fonts_loaded:
        return

    # Imported here to keep this module free of Qt imports at load time
    from qtpy.QtGui import QFontDatabase

    ttf_path = get_bundled_font_path('ttf')
    if osp.isdir(ttf_path):
        for fname in sorted(os.listdir(ttf_path)):
            if fname.endswith('.ttf'):
                QFontDatabase.addApplicationFont(osp.join(ttf_path, fname))

    _bundled_fonts_loaded = True


DEFAULT_SMALL_DELTA = SMALL - MEDIUM
DEFAULT_LARGE_DELTA = SMALL - BIG
