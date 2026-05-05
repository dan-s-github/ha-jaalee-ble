"""The Jaalee BLE integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.const import Platform
from jaalee_ble import JaaleeBluetoothDeviceData, SensorModel

from .const import CONF_SENSOR_MODEL, DEFAULT_SENSOR_MODEL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jaalee BLE device from a config entry."""
    address = entry.unique_id
    if address is None:
        return False
    sensor_model = entry.options.get(
        CONF_SENSOR_MODEL,
        entry.data.get(CONF_SENSOR_MODEL, DEFAULT_SENSOR_MODEL),
    )
    data = _create_device_data(sensor_model)
    coordinator = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (
        PassiveBluetoothProcessorCoordinator(
            hass,
            _LOGGER,
            address=address,
            mode=BluetoothScanningMode.PASSIVE,
            update_method=data.update,
        )
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        coordinator.async_start()
    )  # only start after all platforms have had a chance to subscribe
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _create_device_data(sensor_model: str) -> JaaleeBluetoothDeviceData:
    """Create device data with optional model selection support."""
    try:
        model = SensorModel(sensor_model)
    except ValueError:
        model = SensorModel.SHT20

    try:
        return JaaleeBluetoothDeviceData(sensor_model=model)
    except TypeError:
        _LOGGER.debug(
            "jaalee-ble does not support sensor_model yet; using library default"
        )
        return JaaleeBluetoothDeviceData()
