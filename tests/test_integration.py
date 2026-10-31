"""Test integration setup and unload for Jaalee."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from jaalee_ble import SensorModel
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jaalee import _create_device_data, async_setup_entry
from custom_components.jaalee.const import (
    CONF_SENSOR_MODEL,
    DEFAULT_SENSOR_MODEL,
    DOMAIN,
    SENSOR_MODEL_SHT31,
)


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
    assert entry.runtime_data is mock_coordinator


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


async def test_async_setup_entry_passes_sensor_model_to_device_data(
    hass: HomeAssistant,
) -> None:
    """Test setup passes selected sensor model to device data constructor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="FE:0E:A2:CC:C4:1F",
        options={CONF_SENSOR_MODEL: SENSOR_MODEL_SHT31},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.jaalee.PassiveBluetoothProcessorCoordinator"
        ) as mock_coordinator_class,
        patch(
            "custom_components.jaalee.JaaleeBluetoothDeviceData"
        ) as mock_device_data_class,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
    ):
        mock_coordinator = MagicMock()
        mock_coordinator.async_start = MagicMock(return_value=lambda: None)
        mock_coordinator_class.return_value = mock_coordinator

        mock_device_data = MagicMock()
        mock_device_data.update = MagicMock()
        mock_device_data_class.return_value = mock_device_data

        result = await async_setup_entry(hass, entry)

    assert result is True
    mock_device_data_class.assert_called_once_with(sensor_model=SensorModel.SHT31)


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Test a config entry sets up a coordinator and unloads cleanly."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert isinstance(entry.runtime_data, PassiveBluetoothProcessorCoordinator)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_unload_entry_failure(hass: HomeAssistant) -> None:
    """Test the entry stays loaded-failed when platform unload fails."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=False),
    ):
        assert not await hass.config_entries.async_unload(entry.entry_id)

    assert entry.state is ConfigEntryState.FAILED_UNLOAD


async def test_options_change_reloads_with_new_sensor_model(
    hass: HomeAssistant,
) -> None:
    """Test changing the sensor model reloads the entry with the new model."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="FE:0E:A2:CC:C4:1F",
        data={CONF_SENSOR_MODEL: DEFAULT_SENSOR_MODEL},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.jaalee._create_device_data",
        wraps=_create_device_data,
    ) as create_device_data:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        create_device_data.assert_called_once_with(DEFAULT_SENSOR_MODEL)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_SENSOR_MODEL: SENSOR_MODEL_SHT31},
        )
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    create_device_data.assert_called_with(SENSOR_MODEL_SHT31)
    assert create_device_data.call_count == 2
