"""Jaalee BLE session fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading integrations from custom_components in tests."""


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth: None) -> None:
    """Auto mock bluetooth."""


@pytest.fixture(autouse=True, scope="session")
def mock_bluetooth_history() -> Generator[None]:
    """Patch LinuxAdapters.history which is not mocked on macOS by phcc."""
    with patch(
        "bluetooth_adapters.systems.linux.LinuxAdapters.history",
        new_callable=lambda: property(lambda _self: {}),
    ):
        yield
