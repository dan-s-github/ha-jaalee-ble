"""Config flow for jaalee integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from jaalee_ble import JaaleeBluetoothDeviceData as DeviceData

from .const import (
    CONF_SENSOR_MODEL,
    DEFAULT_SENSOR_MODEL,
    DOMAIN,
    SENSOR_MODEL_SHT20,
    SENSOR_MODEL_SHT31,
    SENSOR_MODELS,
)

SENSOR_MODEL_OPTIONS = {
    SENSOR_MODEL_SHT20: "SHT20",
    SENSOR_MODEL_SHT31: "SHT31",
}


class JaaleeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for jaalee."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: DeviceData | None = None
        self._discovered_devices: dict[str, str] = {}

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> JaaleeOptionsFlow:
        """Get options flow for this handler."""
        return JaaleeOptionsFlow(config_entry)

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        device = DeviceData()
        if not device.supported(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovery_info = discovery_info
        self._discovered_device = device
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        if self._discovered_device is None or self._discovery_info is None:
            return self.async_abort(reason="not_supported")

        device = self._discovered_device
        discovery_info = self._discovery_info
        title = device.title or device.get_device_name() or discovery_info.name
        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={CONF_SENSOR_MODEL: user_input[CONF_SENSOR_MODEL]},
            )

        self._set_confirm_only()
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=placeholders,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSOR_MODEL, default=DEFAULT_SENSOR_MODEL
                    ): vol.In(SENSOR_MODEL_OPTIONS)
                }
            ),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address],
                data={CONF_SENSOR_MODEL: user_input[CONF_SENSOR_MODEL]},
            )

        current_addresses = self._async_current_ids(include_ignore=False)
        discovered_infos: dict[str, BluetoothServiceInfoBleak] = {}
        for connectable in (False, True):
            for discovery_info in async_discovered_service_info(self.hass, connectable):
                discovered_infos.setdefault(discovery_info.address, discovery_info)

        for discovery_info in discovered_infos.values():
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            device = DeviceData()
            if device.supported(discovery_info):
                self._discovered_devices[address] = (
                    device.title or device.get_device_name() or discovery_info.name
                )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices),
                    vol.Required(
                        CONF_SENSOR_MODEL, default=DEFAULT_SENSOR_MODEL
                    ): vol.In(SENSOR_MODEL_OPTIONS),
                }
            ),
        )


class JaaleeOptionsFlow(OptionsFlow):
    """Handle Jaalee options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Jaalee options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_SENSOR_MODEL: user_input[CONF_SENSOR_MODEL]},
            )

        current_model = self._config_entry.options.get(
            CONF_SENSOR_MODEL,
            self._config_entry.data.get(CONF_SENSOR_MODEL, DEFAULT_SENSOR_MODEL),
        )
        default_model = (
            current_model if current_model in SENSOR_MODELS else DEFAULT_SENSOR_MODEL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SENSOR_MODEL, default=default_model): vol.In(
                        SENSOR_MODEL_OPTIONS
                    )
                }
            ),
        )
