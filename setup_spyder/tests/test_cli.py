# -*- coding: utf-8 -*-
from setup_spyder.cli import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.no_launch is False
    assert args.ephemeral is False
    assert args.sem_estilo is False
    assert args.workdir is None


def test_parse_args_flags():
    args = parse_args(
        ["--no-launch", "--ephemeral", "--sem-estilo", "-w", "C:\\proj"]
    )
    assert args.no_launch is True
    assert args.ephemeral is True
    assert args.sem_estilo is True
    assert args.workdir == "C:\\proj"


def test_parse_args_spyder_remainder():
    args = parse_args(["--", "--debug"])
    assert args.spyder_args[0] in ("--", "--debug") or "--debug" in args.spyder_args
