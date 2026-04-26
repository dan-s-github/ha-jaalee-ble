"""Tests for the Jaalee BLE integration."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak


def make_bluetooth_service_info(ad_data: dict[str, Any]) -> BluetoothServiceInfoBleak:
    """Create Bluetooth discovery info from saved advertisement data."""
    discovery_info = cast(
        "BluetoothServiceInfoBleak", MagicMock(spec=BluetoothServiceInfoBleak)
    )
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
    discovery_info.service_uuids = ad_data.get("service_uuids", [])
    discovery_info.source = ad_data.get("source", "test")
    return discovery_info


JAALEE_SERVICE_INFO = make_bluetooth_service_info(
    {
        "name": "FE:0E:A2:CC:C4:1F",
        "address": "FE:0E:A2:CC:C4:1F",
        "rssi": -87,
        "manufacturer_data": {"76": "0215ebefd08370a247c89837e7b5634df52567e48d2ecb64"},
        "service_data": {
            "0000f525-0000-1000-8000-00805f9b34fb": "641fc4cca20efe67e48d2e"
        },
        "service_uuids": ["0000f525-0000-1000-8000-00805f9b34fb"],
        "source": "08:A6:F7:BF:1B:4E",
    }
)

NOT_JAALEE_SERVICE_INFO = make_bluetooth_service_info(
    {
        "name": "Unknown BLE",
        "address": "AA:BB:CC:DD:EE:FF",
        "rssi": -72,
        "manufacturer_data": {"76": "0215ebefd08370a247c89837e7b5634df52500000000cb64"},
        "service_data": {"0000ffff-0000-1000-8000-00805f9b34fb": "010203040506"},
        "service_uuids": ["0000ffff-0000-1000-8000-00805f9b34fb"],
        "source": "local",
    }
)
