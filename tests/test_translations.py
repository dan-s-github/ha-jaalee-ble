"""Test the shipped translations for Jaalee."""

from pathlib import Path

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "jaalee"


def test_translations_have_no_key_references() -> None:
    """
    Test translations contain literal text only.

    Home Assistant resolves [%key:...%] references only for core integrations;
    in a custom integration they are shown to the user verbatim. strings.json
    is checked too, as translations/en.json is generated from it.
    """
    paths = [COMPONENT_DIR / "strings.json", *COMPONENT_DIR.glob("translations/*.json")]
    for path in paths:
        assert "[%key:" not in path.read_text(), path.name
