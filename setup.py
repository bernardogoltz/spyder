# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Spyder (fork bernardogoltz/spyder)
==================================

The Scientific Python Development Environment, Spyder 5.x API.

This fork is published only through Git. The launcher that opens it in a
project's ``.venv`` (``setup-spyder``) and the AI Terminal plugin live in the
separate ``setup-spyder`` distribution (submodule ``setup-spyder/``); this
package must not ship any ``setup_spyder`` module or console script, or the
IDE would shadow the launcher.
"""

from __future__ import print_function

# Standard library imports
import ast
import io
import os
import os.path as osp
import sys

# Third party imports
from setuptools import setup


# =============================================================================
# Minimal Python version sanity check
# Taken from the notebook setup.py -- Modified BSD License
# =============================================================================
v = sys.version_info
if v[0] >= 3 and v[:2] < (3, 8):
    error = "ERROR: Spyder requires Python version 3.8 and above."
    print(error, file=sys.stderr)
    sys.exit(1)


# =============================================================================
# Constants
# =============================================================================
NAME = 'spyder'
LIBNAME = 'spyder'


def _spyder_meta():
    """Read version without importing spyder (PEP 517 isolated builds)."""
    path = osp.join(osp.dirname(osp.abspath(__file__)), 'spyder', '__init__.py')
    info = None
    website = 'https://www.spyder-ide.org/'
    with io.open(path, encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('version_info'):
                info = ast.literal_eval(line.split('=', 1)[1].strip())
            elif line.startswith('__website_url__'):
                website = ast.literal_eval(line.split('=', 1)[1].strip())
            if info is not None and line.startswith('__website_url__'):
                break
    return '.'.join(map(str, info)), website


__version__, __website_url__ = _spyder_meta()


# =============================================================================
# Auxiliary functions
# =============================================================================
def get_package_data(name, extlist):
    """
    Return data files for package *name* with extensions in *extlist*.
    """
    flist = []
    # Workaround to replace os.path.relpath (not available until Python 2.6):
    offset = len(name)+len(os.pathsep)
    for dirpath, _dirnames, filenames in os.walk(name):
        if 'tests' not in dirpath:
            for fname in filenames:
                if (not fname.startswith('.') and
                        osp.splitext(fname)[1] in extlist):
                    flist.append(osp.join(dirpath, fname)[offset:])
    return flist


def get_subpackages(name):
    """
    Return subpackages of package *name*.
    """
    splist = []
    for dirpath, _dirnames, _filenames in os.walk(name):
        if 'tests' not in dirpath:
            if osp.isfile(osp.join(dirpath, '__init__.py')):
                splist.append(".".join(dirpath.split(os.sep)))

    return splist


def get_packages():
    """
    Return package list: only the ``spyder`` package and its subpackages.
    """
    return get_subpackages(LIBNAME)


# =============================================================================
# Files added to the package
# =============================================================================
EXTLIST = ['.pot', '.po', '.mo', '.svg', '.png', '.css', '.html', '.js',
           '.ini', '.txt', '.qss', '.ttf', '.json', '.rst', '.bloom',
           '.ico', '.gif', '.mp3', '.ogg', '.sfd', '.bat', '.sh']


# =============================================================================
# Use Readme for long description
# =============================================================================
with io.open('README.md', encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()


#==============================================================================
# Setup arguments
#==============================================================================
setup_args = dict(
    name=NAME,
    version=__version__,
    description='The Scientific Python Development Environment '
                '(bernardogoltz fork, Spyder 5.x API)',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    download_url='https://github.com/bernardogoltz/spyder',
    author="The Spyder Project Contributors",
    author_email="spyder.python@gmail.com",
    url=__website_url__,
    license='MIT',
    keywords='PyQt5 editor console widgets IDE science data analysis IPython',
    platforms=["Windows", "Linux", "Mac OS-X"],
    packages=get_packages(),
    package_data={LIBNAME: get_package_data(LIBNAME, EXTLIST)},
    python_requires='>=3.8',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Widget Sets',
    ],
)


install_requires = [
    'applaunchservices>=0.3.0;platform_system=="Darwin"',
    'atomicwrites>=1.2.0',
    'chardet>=2.0.0',
    'cloudpickle>=0.5.0',
    'cookiecutter>=1.6.0',
    'diff-match-patch>=20181111',
    # While this is only required for python <3.10, it is safe enough to
    # install in all cases and helps the tests to pass.
    'importlib-metadata>=4.6.0',
    'intervaltree>=3.0.2',
    'ipython>=8.12.2,<8.13.0; python_version=="3.8"',
    'ipython>=8.13.0,<9.0.0,!=8.17.1; python_version>"3.8"',
    'jedi>=0.17.2,<0.20.0',
    'jellyfish>=0.7',
    'jsonschema>=3.2.0',
    'keyring>=17.0.0',
    'nbconvert>=4.0',
    'numpydoc>=0.6.0',
    # Required to get SSH connections to remote kernels
    'paramiko>=2.4.0;platform_system=="Windows"',
    'parso>=0.7.0,<0.9.0',
    'pexpect>=4.4.0',
    'pickleshare>=0.4',
    'psutil>=5.3',
    'pygments>=2.0',
    'pylint>=3.1,<4',
    'pylint-venv>=3.0.2',
    'python-lsp-black>=2.0.0,<3.0.0',
    'pyls-spyder>=0.4.0',
    'pyqt5>=5.10,<5.16',
    'pyqtwebengine>=5.10,<5.16',
    'python-lsp-server[all]>=1.12.0,<1.13.0',
    'pyxdg>=0.26;platform_system=="Linux"',
    'pyzmq>=24.0.0',
    'qdarkstyle>=3.2.0,<3.3.0',
    'qstylizer>=0.2.2',
    'qtawesome>=1.3.1,<1.4.0',
    'qtconsole>=5.5.1,<5.6.0',
    'qtpy>=2.1.0',
    'rtree>=0.9.7',
    'setuptools>=49.6.0',
    'sphinx>=0.6.6',
    'spyder-kernels>=2.5.2,<2.6.0',
    'textdistance>=4.2.0',
    'three-merge>=0.1.1',
    'watchdog>=0.10.3',
]

# Loosen constraints to ensure dev versions still work
if 'dev' in __version__:
    reqs_to_loosen = {'python-lsp-server[all]', 'qtconsole', 'spyder-kernels'}
    install_requires = [req for req in install_requires
                        if req.split(">")[0] not in reqs_to_loosen]
    install_requires.append('python-lsp-server[all]>=1.12.0,<1.14.0')
    install_requires.append('qtconsole>=5.5.1,<5.7.0')
    install_requires.append('spyder-kernels>=2.5.2,<2.7.0')

extras_require = {
    'test': [
        'pywin32; platform_system == "Windows"',
        'coverage',
        'cython',
        'flaky',
        'matplotlib',
        'pandas',
        'pillow',
        'pytest<8.0',
        'pytest-cov',
        'pytest-lazy-fixture',
        'pytest-mock',
        'pytest-order',
        'pytest-qt',
        'pytest-timeout',
        'pyyaml',
        'scipy',
        'sympy',
    ],
}


spyder_plugins_entry_points = [
    'appearance = spyder.plugins.appearance.plugin:Appearance',
    'application = spyder.plugins.application.plugin:Application',
    'breakpoints = spyder.plugins.breakpoints.plugin:Breakpoints',
    'completions = spyder.plugins.completion.plugin:CompletionPlugin',
    'editor = spyder.plugins.editor.plugin:Editor',
    'explorer = spyder.plugins.explorer.plugin:Explorer',
    'find_in_files = spyder.plugins.findinfiles.plugin:FindInFiles',
    'help = spyder.plugins.help.plugin:Help',
    'historylog = spyder.plugins.history.plugin:HistoryLog',
    'internal_console = spyder.plugins.console.plugin:Console',
    'ipython_console = spyder.plugins.ipythonconsole.plugin:IPythonConsole',
    'layout = spyder.plugins.layout.plugin:Layout',
    'main_interpreter = spyder.plugins.maininterpreter.plugin:MainInterpreter',
    'mainmenu = spyder.plugins.mainmenu.plugin:MainMenu',
    'onlinehelp = spyder.plugins.onlinehelp.plugin:OnlineHelp',
    'outline_explorer = spyder.plugins.outlineexplorer.plugin:OutlineExplorer',
    'plots = spyder.plugins.plots.plugin:Plots',
    'preferences = spyder.plugins.preferences.plugin:Preferences',
    'profiler = spyder.plugins.profiler.plugin:Profiler',
    'project_explorer = spyder.plugins.projects.plugin:Projects',
    'pylint = spyder.plugins.pylint.plugin:Pylint',
    'pythonpath_manager = spyder.plugins.pythonpath.plugin:PythonpathManager',
    'run = spyder.plugins.run.plugin:Run',
    'shortcuts = spyder.plugins.shortcuts.plugin:Shortcuts',
    'statusbar = spyder.plugins.statusbar.plugin:StatusBar',
    'toolbar = spyder.plugins.toolbar.plugin:Toolbar',
    'tours = spyder.plugins.tours.plugin:Tours',
    'variable_explorer = spyder.plugins.variableexplorer.plugin:VariableExplorer',
    'workingdir = spyder.plugins.workingdirectory.plugin:WorkingDirectory',
]

spyder_completions_entry_points = [
    ('fallback = spyder.plugins.completion.providers.fallback.provider:'
     'FallbackProvider'),
    ('snippets = spyder.plugins.completion.providers.snippets.provider:'
     'SnippetsProvider'),
    ('lsp = spyder.plugins.completion.providers.languageserver.provider:'
     'LanguageServerProvider'),
]


setup_args['install_requires'] = install_requires
setup_args['extras_require'] = extras_require
setup_args['entry_points'] = {
    'gui_scripts': [
            'spyder = spyder.app.start:main'
    ],
    'spyder.plugins': spyder_plugins_entry_points,
    'spyder.completions': spyder_completions_entry_points
}


# =============================================================================
# Main setup
# =============================================================================
setup(**setup_args)
