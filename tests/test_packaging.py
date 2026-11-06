from __future__ import annotations

from importlib.metadata import version
from importlib.resources import files

from woodpecker_mcp import __version__


def test_py_typed_marker_is_packaged():
    assert (files("woodpecker_mcp") / "py.typed").is_file()


def test_version_matches_installed_metadata():
    assert __version__ == version("woodpecker-mcp")
