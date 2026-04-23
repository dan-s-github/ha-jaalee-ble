"""Test device module for jaalee integration."""

from unittest.mock import MagicMock

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothEntityKey,
)

from custom_components.jaalee.device import device_key_to_bluetooth_entity_key


def test_device_key_to_bluetooth_entity_key() -> None:
    """Test conversion of device key to bluetooth entity key."""
    # Create a mock device key with key and device_id attributes
    mock_device_key = MagicMock()
    mock_device_key.key = "test_sensor"
    mock_device_key.device_id = "device_123"

    result = device_key_to_bluetooth_entity_key(mock_device_key)

    # Verify the result is a PassiveBluetoothEntityKey
    assert isinstance(result, PassiveBluetoothEntityKey)
    # Verify the converted key and device_id match
    assert result.key == "test_sensor"
    assert result.device_id == "device_123"


def test_device_key_to_bluetooth_entity_key_with_different_values() -> None:
    """Test conversion with different key and device_id values."""
    mock_device_key = MagicMock()
    mock_device_key.key = "temperature_celsius"
    mock_device_key.device_id = "jaalee_ble_abc123"

    result = device_key_to_bluetooth_entity_key(mock_device_key)

    assert result.key == "temperature_celsius"
    assert result.device_id == "jaalee_ble_abc123"


def test_device_key_to_bluetooth_entity_key_preserves_empty_strings() -> None:
    """Test conversion preserves empty string values."""
    mock_device_key = MagicMock()
    mock_device_key.key = ""
    mock_device_key.device_id = ""

    result = device_key_to_bluetooth_entity_key(mock_device_key)

    assert result.key == ""
    assert result.device_id == ""
