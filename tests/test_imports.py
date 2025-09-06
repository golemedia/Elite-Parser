# tests/test_imports.py
import importlib


def test_import_eliteparser():
    """Elite Parser core module should import without side-effects or crashes."""
    importlib.import_module("eliteparser")
