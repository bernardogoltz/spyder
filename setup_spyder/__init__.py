# -*- coding: utf-8 -*-
"""Launcher do Spyder 5.x no venv do projeto (uv), sem conda."""

from __future__ import annotations

__version__ = "0.1.0"

from .cli import launch, main

open_spyder = launch

__all__ = ["__version__", "launch", "main", "open_spyder"]
