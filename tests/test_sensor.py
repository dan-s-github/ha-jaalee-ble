"""Test sensor module for jaalee integration."""

from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
)
from jaalee_ble import SensorDeviceClass as JaaleeSensorDeviceClass
from jaalee_ble import Units

from custom_components.jaalee.sensor import (
    CUSTOM_SENSOR_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS,
    TX_POWER_KEY,
    sensor_update_to_bluetooth_data_update,
)


def test_sensor_descriptions_exist() -> None:
    """Test that sensor descriptions are defined."""
    assert len(SENSOR_DESCRIPTIONS) > 0


def test_battery_sensor_description() -> None:
    """Test battery sensor description."""
    key = (JaaleeSensorDeviceClass.BATTERY, Units.PERCENTAGE)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.BATTERY
    assert description.native_unit_of_measurement == PERCENTAGE
    assert description.state_class == SensorStateClass.MEASUREMENT
    assert description.entity_category == EntityCategory.DIAGNOSTIC


def test_temperature_sensor_description() -> None:
    """Test temperature sensor description."""
    key = (JaaleeSensorDeviceClass.TEMPERATURE, Units.TEMP_CELSIUS)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.TEMPERATURE
    assert description.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert description.state_class == SensorStateClass.MEASUREMENT


def test_humidity_sensor_description() -> None:
    """Test humidity sensor description."""
    key = (JaaleeSensorDeviceClass.HUMIDITY, Units.PERCENTAGE)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.HUMIDITY
    assert description.native_unit_of_measurement == PERCENTAGE
    assert description.state_class == SensorStateClass.MEASUREMENT


def test_co2_sensor_description() -> None:
    """Test CO2 sensor description."""
    key = (JaaleeSensorDeviceClass.CO2, Units.CONCENTRATION_PARTS_PER_MILLION)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.CO2
    assert description.native_unit_of_measurement == CONCENTRATION_PARTS_PER_MILLION


def test_voltage_sensor_description() -> None:
    """Test voltage sensor description."""
    key = (JaaleeSensorDeviceClass.VOLTAGE, Units.ELECTRIC_POTENTIAL_VOLT)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.VOLTAGE
    assert description.native_unit_of_measurement == UnitOfElectricPotential.VOLT
    assert description.entity_category == EntityCategory.DIAGNOSTIC
    assert description.entity_registry_enabled_default is False
    assert description.suggested_display_precision == 3


def test_pressure_sensor_description() -> None:
    """Test pressure sensor description."""
    key = (JaaleeSensorDeviceClass.PRESSURE, Units.PRESSURE_HPA)
    assert key in SENSOR_DESCRIPTIONS

    description = SENSOR_DESCRIPTIONS[key]
    assert description.device_class == SensorDeviceClass.PRESSURE
    assert description.native_unit_of_measurement == UnitOfPressure.HPA


def test_custom_sensor_descriptions() -> None:
    """Test custom sensor descriptions."""
    assert TX_POWER_KEY in CUSTOM_SENSOR_DESCRIPTIONS

    description = CUSTOM_SENSOR_DESCRIPTIONS[TX_POWER_KEY]
    assert description.device_class == SensorDeviceClass.SIGNAL_STRENGTH
    assert description.native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    assert description.entity_category == EntityCategory.DIAGNOSTIC
    assert description.entity_registry_enabled_default is False


def test_sensor_update_to_bluetooth_data_update_empty() -> None:
    """Test conversion of empty sensor update."""
    mock_sensor_update = MagicMock()
    mock_sensor_update.devices = {}
    mock_sensor_update.entity_descriptions = {}
    mock_sensor_update.entity_values = {}

    result = sensor_update_to_bluetooth_data_update(mock_sensor_update)

    assert result.devices == {}
    assert result.entity_descriptions == {}
    assert result.entity_data == {}
    assert result.entity_names == {}


def test_sensor_update_to_bluetooth_data_update_with_battery() -> None:
    """Test conversion with battery sensor."""
    mock_device_key = MagicMock()
    mock_device_key.key = f"{JaaleeSensorDeviceClass.BATTERY}_{Units.PERCENTAGE}"
    mock_device_key.device_id = "device_123"

    mock_description = MagicMock()
    mock_description.device_class = JaaleeSensorDeviceClass.BATTERY
    mock_description.native_unit_of_measurement = Units.PERCENTAGE

    mock_sensor_value = MagicMock()
    mock_sensor_value.native_value = 85
    mock_sensor_value.name = "Battery"

    mock_sensor_update = MagicMock()
    mock_sensor_update.devices = {}
    mock_sensor_update.entity_descriptions = {mock_device_key: mock_description}
    mock_sensor_update.entity_values = {mock_device_key: mock_sensor_value}

    with patch(
        "custom_components.jaalee.sensor.device_key_to_bluetooth_entity_key"
    ) as mock_convert:
        mock_entity_key = MagicMock()
        mock_convert.return_value = mock_entity_key

        with patch(
            "custom_components.jaalee.sensor.sensor_device_info_to_hass_device_info"
        ):
            sensor_update_to_bluetooth_data_update(mock_sensor_update)

            # Verify the entity key conversion was called
            assert mock_convert.called


def test_sensor_update_to_bluetooth_data_update_filters_unsupported() -> None:
    """Test that unsupported sensors are filtered out."""
    mock_device_key = MagicMock()
    mock_device_key.key = "unsupported_sensor"
    mock_device_key.device_id = "device_123"

    mock_description = MagicMock()
    mock_description.device_class = "UNSUPPORTED"
    mock_description.native_unit_of_measurement = "UNIT"

    mock_sensor_update = MagicMock()
    mock_sensor_update.devices = {}
    mock_sensor_update.entity_descriptions = {mock_device_key: mock_description}
    mock_sensor_update.entity_values = {}

    result = sensor_update_to_bluetooth_data_update(mock_sensor_update)

    # Unsupported sensors should not be in the result
    assert result.entity_descriptions == {}


def test_tx_power_key_value() -> None:
    """Test that TX_POWER_KEY has the expected value."""
    assert TX_POWER_KEY == "tx_power"
