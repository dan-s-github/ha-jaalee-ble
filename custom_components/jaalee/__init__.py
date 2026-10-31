"""The Jaalee BLE integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from jaalee_ble import JaaleeBluetoothDeviceData, SensorModel

from .const import CONF_SENSOR_MODEL, DEFAULT_SENSOR_MODEL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

type JaaleeConfigEntry = ConfigEntry[PassiveBluetoothProcessorCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: JaaleeConfigEntry) -> bool:
    """Set up Jaalee BLE device from a config entry."""
    address = entry.unique_id
    if address is None:
        return False
    sensor_model = entry.options.get(
        CONF_SENSOR_MODEL,
        entry.data.get(CONF_SENSOR_MODEL, DEFAULT_SENSOR_MODEL),
    )
    data = _create_device_data(sensor_model)
    coordinator = entry.runtime_data = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=data.update,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        coordinator.async_start()
    )  # only start after all platforms have had a chance to subscribe
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JaaleeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _create_device_data(sensor_model: str) -> JaaleeBluetoothDeviceData:
    """Create device data for the selected sensor model."""
    try:
        model = SensorModel(sensor_model)
    except ValueError:
        model = SensorModel.SHT20
    return JaaleeBluetoothDeviceData(sensor_model=model)
