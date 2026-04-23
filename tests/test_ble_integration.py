"""Integration tests for Jaalee BLE using real BLE advertisements."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.jaalee import async_setup_entry
from custom_components.jaalee.config_flow import JaaleeConfigFlow
from custom_components.jaalee.const import DOMAIN


@pytest.fixture
def ble_advertisements() -> list[dict]:
    """Load real BLE advertisements from test file."""
    test_file = Path(__file__).parent / "test_ble_advertisements.json"
    with test_file.open() as f:
        return json.load(f)


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_jaalee"
    entry.unique_id = "FE:0E:A2:CC:C4:1F"
    entry.async_on_unload = MagicMock()
    return entry


def test_load_advertisements() -> None:
    """Test that BLE advertisements are properly loaded."""
    test_file = Path(__file__).parent / "test_ble_advertisements.json"
    assert test_file.exists(), "Test advertisements file not found"

    with test_file.open() as f:
        ads = json.load(f)

    assert len(ads) == 6, "Should have 6 sample advertisements"
    assert all(ad["address"] == "FE:0E:A2:CC:C4:1F" for ad in ads)
    assert all("manufacturer_data" in ad for ad in ads)
    assert all("service_data" in ad for ad in ads)


def test_advertisements_have_required_fields(ble_advertisements: list[dict]) -> None:
    """Test that all advertisements have required fields."""
    required_fields = ["name", "address", "rssi", "manufacturer_data", "service_data"]

    for ad in ble_advertisements:
        for field in required_fields:
            assert field in ad, f"Advertisement missing required field: {field}"


def test_all_advertisements_same_device(ble_advertisements: list[dict]) -> None:
    """Test that all advertisements are from the same device."""
    addresses = {ad["address"] for ad in ble_advertisements}
    assert len(addresses) == 1, "All advertisements should be from same device"
    assert "FE:0E:A2:CC:C4:1F" in addresses


def test_manufacturer_data_format(ble_advertisements: list[dict]) -> None:
    """Test that manufacturer data is properly formatted."""
    for ad in ble_advertisements:
        manufacturer_data = ad.get("manufacturer_data", {})
        assert isinstance(manufacturer_data, dict)
        assert "76" in manufacturer_data, "Apple manufacturer ID should be present"
        # Apple iBeacon manufacturer data should be 20 bytes (40 hex chars)
        assert isinstance(manufacturer_data["76"], str)
        assert len(manufacturer_data["76"]) >= 40


def test_service_data_format(ble_advertisements: list[dict]) -> None:
    """Test that service data is properly formatted."""
    for ad in ble_advertisements:
        service_data = ad.get("service_data", {})
        assert isinstance(service_data, dict)
        # Should have the Jaalee service UUID
        jaalee_uuid = "0000f525-0000-1000-8000-00805f9b34fb"
        assert jaalee_uuid in service_data


def test_rssi_values_valid(ble_advertisements: list[dict]) -> None:
    """Test that RSSI values are within valid range."""
    for ad in ble_advertisements:
        rssi = ad.get("rssi")
        assert rssi is not None
        assert isinstance(rssi, int)
        # RSSI should be negative and within typical range
        assert -100 <= rssi <= 0


@pytest.mark.asyncio
async def test_config_flow_with_real_advertisement(
    ble_advertisements: list[dict],
) -> None:
    """Test config flow discovery with real BLE advertisement."""
    # Use first advertisement for testing
    ad_data = ble_advertisements[0]

    config_flow = JaaleeConfigFlow()
    config_flow.hass = MagicMock()
    config_flow.async_set_unique_id = AsyncMock()
    config_flow._abort_if_unique_id_configured = MagicMock()  # noqa: SLF001

    # Create a BluetoothServiceInfoBleak-like object from advertisement
    discovery_info = MagicMock(spec=BluetoothServiceInfoBleak)
    discovery_info.address = ad_data["address"]
    discovery_info.name = ad_data["name"]
    discovery_info.rssi = ad_data["rssi"]
    discovery_info.manufacturer_data = {
        int(mfg_id): bytes.fromhex(data)
        for mfg_id, data in ad_data.get("manufacturer_data", {}).items()
    }
    discovery_info.service_data = {
        uuid: bytes.fromhex(data)
        for uuid, data in ad_data.get("service_data", {}).items()
    }
    discovery_info.source = ad_data.get("source", "test")

    with patch(
        "custom_components.jaalee.config_flow.DeviceData"
    ) as mock_device_data_class:
        mock_device = MagicMock()
        mock_device.supported.return_value = True
        mock_device.title = "Jaalee Device"
        mock_device.get_device_name.return_value = "Jaalee"
        mock_device_data_class.return_value = mock_device

        config_flow.async_step_bluetooth_confirm = AsyncMock(
            return_value={"type": "form"}
        )

        await config_flow.async_step_bluetooth(discovery_info)

        # Verify unique ID was set with correct address
        config_flow.async_set_unique_id.assert_called_once_with(ad_data["address"])
        # Verify device was checked for support
        assert mock_device.supported.called


@pytest.mark.asyncio
async def test_multiple_advertisement_processing(
    ble_advertisements: list[dict],
) -> None:
    """Test processing multiple advertisements from same device."""
    # All advertisements are from same device
    device_addresses = {ad["address"] for ad in ble_advertisements}
    assert len(device_addresses) == 1

    # Verify each advertisement has expected structure
    for ad in ble_advertisements:
        assert ad["address"] == "FE:0E:A2:CC:C4:1F"
        assert ad["rssi"] is not None
        assert "manufacturer_data" in ad
        assert "service_data" in ad
        assert "time" in ad


def test_advertisement_rssi_variation(ble_advertisements: list[dict]) -> None:
    """Test that advertisements show typical RSSI variation."""
    rssi_values = [ad["rssi"] for ad in ble_advertisements]

    # Should have multiple different RSSI values (signal strength variation)
    assert len(set(rssi_values)) > 1, "Should have RSSI variation"

    # Typical range for BLE devices
    assert all(-100 <= rssi <= 0 for rssi in rssi_values)
    assert max(rssi_values) > -90  # At least some strong signals
    assert min(rssi_values) < -75  # At least some weak signals


def test_advertisement_time_progression(ble_advertisements: list[dict]) -> None:
    """Test that advertisements are timestamped in order."""
    times = [ad["time"] for ad in ble_advertisements]

    # Times should generally progress (allowing for some clock variation)
    for i in range(1, len(times)):
        time_delta = times[i] - times[i - 1]
        # Allow for time going backwards by up to 1 second (clock drift)
        # but generally should progress
        assert time_delta > -1


@pytest.mark.asyncio
async def test_integration_setup_with_advertisement_device(
    mock_hass: MagicMock, mock_config_entry: MagicMock, ble_advertisements: list[dict]
) -> None:
    """Test full integration setup for device from advertisements."""
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

        # Set unique_id from actual advertisement
        mock_config_entry.unique_id = ble_advertisements[0]["address"]

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        # Verify coordinator was set up for the device address
        coordinator_call = mock_coordinator_class.call_args
        assert coordinator_call.kwargs["address"] == "FE:0E:A2:CC:C4:1F"


def test_service_uuid_consistency(ble_advertisements: list[dict]) -> None:
    """Test that all advertisements use consistent Jaalee service UUID."""
    expected_uuid = "0000f525-0000-1000-8000-00805f9b34fb"

    for ad in ble_advertisements:
        service_uuids = ad.get("service_uuids", [])
        assert expected_uuid in service_uuids, "Jaalee UUID should be in service_uuids"

        service_data = ad.get("service_data", {})
        assert expected_uuid in service_data, "Jaalee UUID should be in service_data"


def test_raw_advertisement_data(ble_advertisements: list[dict]) -> None:
    """Test that raw BLE advertisement data is present and valid."""
    for ad in ble_advertisements:
        raw = ad.get("raw")
        assert raw is not None, "Raw advertisement data should be present"
        assert isinstance(raw, str), "Raw data should be hex string"
        # Should be valid hex
        try:
            bytes.fromhex(raw)
        except ValueError:
            pytest.fail(f"Raw data is not valid hex: {raw}")
