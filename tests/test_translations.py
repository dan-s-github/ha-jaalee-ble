"""Test the shipped translations for Jaalee."""

from pathlib import Path

TRANSLATIONS_DIR = (
    Path(__file__).parent.parent / "custom_components" / "jaalee" / "translations"
)


def test_translations_have_no_key_references() -> None:
    """
    Test translations contain literal text only.

    Home Assistant resolves [%key:...%] references only for core integrations;
    in a custom integration they are shown to the user verbatim.
    """
    for path in TRANSLATIONS_DIR.glob("*.json"):
        assert "[%key:" not in path.read_text(), path.name
