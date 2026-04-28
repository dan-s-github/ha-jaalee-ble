"""Test integration setup and unload for Jaalee."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jaalee import async_setup_entry, async_unload_entry
from custom_components.jaalee.const import DOMAIN


async def test_async_setup_entry_success(hass: HomeAssistant) -> None:
    """Test successful setup of a config entry."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.jaalee.PassiveBluetoothProcessorCoordinator"
        ) as mock_coordinator_class,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_start = MagicMock(return_value=lambda: None)
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.entry_id in hass.data[DOMAIN]


async def test_async_setup_entry_no_unique_id(hass: HomeAssistant) -> None:
    """Test setup fails when config entry has no unique_id."""
    entry = MockConfigEntry(domain=DOMAIN)

    result = await async_setup_entry(hass, entry)

    assert result is False


async def test_async_setup_entry_creates_coordinator(hass: HomeAssistant) -> None:
    """Test that setup creates coordinator with the entry unique_id address."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.jaalee.PassiveBluetoothProcessorCoordinator"
        ) as mock_coordinator_class,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_start = MagicMock(return_value=lambda: None)
        mock_coordinator_class.return_value = mock_coordinator

        await async_setup_entry(hass, entry)

    call_kwargs = mock_coordinator_class.call_args.kwargs
    assert call_kwargs["address"] == "FE:0E:A2:CC:C4:1F"


async def test_async_unload_entry_success(hass: HomeAssistant) -> None:
    """Test successful unload of a config entry."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=True),
    ):
        result = await async_unload_entry(hass, entry)

    assert result is True
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_async_unload_entry_failure(hass: HomeAssistant) -> None:
    """Test unload when platform unload fails."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=False),
    ):
        result = await async_unload_entry(hass, entry)

    assert result is False
    assert entry.entry_id in hass.data[DOMAIN]
