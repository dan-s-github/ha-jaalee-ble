"""Test integration setup and unload for jaalee."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.jaalee import async_setup_entry, async_unload_entry
from custom_components.jaalee.const import DOMAIN


@pytest.fixture
def mock_hass() -> None:
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_config_entry() -> None:
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_123"
    entry.unique_id = "AA:BB:CC:DD:EE:FF"
    entry.async_on_unload = MagicMock()
    return entry


@pytest.mark.asyncio
async def test_async_setup_entry_success(mock_hass, mock_config_entry) -> None:
    """Test successful setup of a config entry."""
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    with (
        patch("custom_components.jaalee.JaaleeBluetoothDeviceData"),
        patch(
            "custom_components.jaalee.PassiveBluetoothProcessorCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_start = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once()
        mock_config_entry.async_on_unload.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry_no_unique_id(mock_hass, mock_config_entry) -> None:
    """Test setup fails when config entry has no unique_id."""
    mock_config_entry.unique_id = None

    result = await async_setup_entry(mock_hass, mock_config_entry)

    assert result is False


@pytest.mark.asyncio
async def test_async_setup_entry_creates_coordinator(
    mock_hass: MagicMock, mock_config_entry: MagicMock
) -> None:
    """Test that setup creates a PassiveBluetoothProcessorCoordinator."""
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    with (
        patch("custom_components.jaalee.JaaleeBluetoothDeviceData"),
        patch(
            "custom_components.jaalee.PassiveBluetoothProcessorCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_start = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        await async_setup_entry(mock_hass, mock_config_entry)

        # Verify coordinator was created with correct parameters
        mock_coordinator_class.assert_called_once()
        call_kwargs = mock_coordinator_class.call_args.kwargs
        assert call_kwargs["address"] == mock_config_entry.unique_id


@pytest.mark.asyncio
async def test_async_unload_entry_success(mock_hass, mock_config_entry) -> None:
    """Test successful unload of a config entry."""
    mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()
    mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
    mock_hass.config_entries.async_unload_platforms.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry_failure(mock_hass, mock_config_entry) -> None:
    """Test unload when platform unload fails."""
    mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is False


@pytest.mark.asyncio
async def test_async_unload_entry_removes_coordinator(
    mock_hass: MagicMock, mock_config_entry: MagicMock
) -> None:
    """Test that unload removes the coordinator from hass data."""
    mock_coordinator = MagicMock()
    mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator
    mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    await async_unload_entry(mock_hass, mock_config_entry)

    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
