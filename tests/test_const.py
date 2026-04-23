"""Test constants for jaalee integration."""

from custom_components.jaalee.const import DOMAIN


def test_domain_constant() -> None:
    """Test that DOMAIN constant is correctly defined."""
    assert DOMAIN == "jaalee"
    assert isinstance(DOMAIN, str)
    assert len(DOMAIN) > 0
