"""Support for Jaalee BLE sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info
from jaalee_ble import SensorDeviceClass as JaaleeSensorDeviceClass
from jaalee_ble import SensorUpdate, Units

from .const import DOMAIN
from .device import device_key_to_bluetooth_entity_key

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

UID_TX_POWER_KEY = "uid_tx_power"

JAALEE_LIGHT_DEVICE_CLASS = getattr(
    JaaleeSensorDeviceClass,
    "LIGHT",
    getattr(JaaleeSensorDeviceClass, "ILLUMINANCE", None),
)

# Sensor type configurations for Home Assistant integration.
#
# CURRENT PARSER CAPABILITIES (jaalee-ble v1.0.0rc1):
#   Battery percentage, Humidity percentage, Temperature (Celsius)
#
# FORWARD-LOOKING CONFIGURATIONS (Ready when parser adds support):
#   CO2 (ppm): Awaiting parser support for CO2 extraction
#   Voltage (V): Awaiting parser support for voltage extraction
#   Illuminance (lx): Prepared for JHTPUL and similar devices
#
# PLANNED FUTURE SENSORS (When jaalee-ble parser adds JHTPUL support):
#   Pressure (hPa): For JHTPUL device integration
#   UV Index: For JHTPUL device integration
#
# The parsing logic in sensor_update_to_bluetooth_data_update() ensures that
# only sensor types actually provided by the parser will create Home Assistant
# entities, so forward-looking configurations don't cause issues.
#
SENSOR_DESCRIPTIONS = {
    (JaaleeSensorDeviceClass.BATTERY, Units.PERCENTAGE): SensorEntityDescription(
        key=f"{JaaleeSensorDeviceClass.BATTERY}_{Units.PERCENTAGE}",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    (
        JaaleeSensorDeviceClass.CO2,
        Units.CONCENTRATION_PARTS_PER_MILLION,
    ): SensorEntityDescription(
        key=(f"{JaaleeSensorDeviceClass.CO2}_{Units.CONCENTRATION_PARTS_PER_MILLION}"),
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (JaaleeSensorDeviceClass.HUMIDITY, Units.PERCENTAGE): SensorEntityDescription(
        key=f"{JaaleeSensorDeviceClass.HUMIDITY}_{Units.PERCENTAGE}",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (
        JaaleeSensorDeviceClass.TEMPERATURE,
        Units.TEMP_CELSIUS,
    ): SensorEntityDescription(
        key=f"{JaaleeSensorDeviceClass.TEMPERATURE}_{Units.TEMP_CELSIUS}",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (
        JaaleeSensorDeviceClass.VOLTAGE,
        Units.ELECTRIC_POTENTIAL_VOLT,
    ): SensorEntityDescription(
        key=f"{JaaleeSensorDeviceClass.VOLTAGE}_{Units.ELECTRIC_POTENTIAL_VOLT}",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=3,
    ),
    (
        JaaleeSensorDeviceClass.PRESSURE,
        Units.PRESSURE_HPA,
    ): SensorEntityDescription(
        key=f"{JaaleeSensorDeviceClass.PRESSURE}_{Units.PRESSURE_HPA}",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

CUSTOM_SENSOR_DESCRIPTIONS = {
    UID_TX_POWER_KEY: SensorEntityDescription(
        key=UID_TX_POWER_KEY,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
}

if JAALEE_LIGHT_DEVICE_CLASS is not None:
    SENSOR_DESCRIPTIONS[(JAALEE_LIGHT_DEVICE_CLASS, Units.LIGHT_LUX)] = (
        SensorEntityDescription(
            key=f"{JAALEE_LIGHT_DEVICE_CLASS}_{Units.LIGHT_LUX}",
            device_class=SensorDeviceClass.ILLUMINANCE,
            native_unit_of_measurement=LIGHT_LUX,
            state_class=SensorStateClass.MEASUREMENT,
        )
    )


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a bluetooth data update."""
    supported_device_keys = {
        device_key
        for device_key, description in sensor_update.entity_descriptions.items()
        if device_key.key in CUSTOM_SENSOR_DESCRIPTIONS
        or (
            description.device_class
            and description.native_unit_of_measurement
            and (description.device_class, description.native_unit_of_measurement)
            in SENSOR_DESCRIPTIONS
        )
    }

    return PassiveBluetoothDataUpdate(
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        entity_descriptions={
            device_key_to_bluetooth_entity_key(device_key): (
                CUSTOM_SENSOR_DESCRIPTIONS[device_key.key]
                if device_key.key in CUSTOM_SENSOR_DESCRIPTIONS
                else SENSOR_DESCRIPTIONS[
                    (description.device_class, description.native_unit_of_measurement)
                ]
            )
            for device_key, description in sensor_update.entity_descriptions.items()
            if device_key in supported_device_keys
        },
        entity_data={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.entity_values.items()
            if device_key in supported_device_keys
        },
        entity_names={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
            if device_key in supported_device_keys
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Jaalee BLE sensors."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    entry.async_on_unload(
        processor.async_add_entities_listener(
            JaaleeBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(coordinator.async_register_processor(processor))


class JaaleeBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[float | int | None, SensorUpdate]
    ],
    SensorEntity,
):
    """Representation of a Jaalee sensor."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
