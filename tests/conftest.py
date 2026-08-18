"""Jaalee BLE session fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import homeassistant.components.bluetooth as bluetooth_component
import pytest
from habluetooth import scanner_bleak


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading integrations from custom_components in tests."""


@pytest.fixture(autouse=True)
def mock_ha_scanner_start() -> Generator[None]:
    """
    Stop enable_bluetooth's real scanner setup from touching bleak/dbus_fast.

    phcc's enable_bluetooth fixture patches habluetooth.scanner.HaScanner, but
    homeassistant.components.bluetooth imports the class directly from
    habluetooth.scanner_bleak, so that patch misses it: async_start() then
    tries a real scan and fails with "No module named 'dbus_fast'" on macOS,
    skipping the async_stop unload registration and leaving a lingering timer.
    """

    class _NoStartHaScanner(scanner_bleak.HaScanner):
        def async_setup(self) -> None:
            return None

        async def async_start(self) -> None:
            return None

        async def async_stop(self) -> None:
            return None

    with patch.object(bluetooth_component, "HaScanner", _NoStartHaScanner):
        yield


@pytest.fixture(autouse=True)
def mock_bluetooth(mock_ha_scanner_start: None, enable_bluetooth: None) -> None:
    """Auto mock bluetooth."""


@pytest.fixture(autouse=True, scope="session")
def mock_bluetooth_history() -> Generator[None]:
    """Patch LinuxAdapters.history which is not mocked on macOS by phcc."""
    with patch(
        "bluetooth_adapters.systems.linux.LinuxAdapters.history",
        new_callable=lambda: property(lambda _self: {}),
    ):
        yield
