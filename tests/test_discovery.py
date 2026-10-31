"""End-to-end Bluetooth discovery tests for Jaalee."""

import json
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from habluetooth import BluetoothServiceInfoBleak, get_manager
from homeassistant.config_entries import SOURCE_BLUETOOTH
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery_flow

from custom_components.jaalee.const import DOMAIN


@pytest.fixture(autouse=True)
def only_jaalee_discovery() -> Generator[None]:
    """
    Drop discovery flows for other integrations.

    Jaalee advertisements are iBeacons, so the built-in ibeacon integration
    matches them too; its requirements aren't installed in the test env.
    """
    real_create_flow = discovery_flow.async_create_flow

    def _create_flow(
        hass: HomeAssistant, domain: str, *args: Any, **kwargs: Any
    ) -> None:
        if domain == DOMAIN:
            real_create_flow(hass, domain, *args, **kwargs)

    with patch(
        "homeassistant.components.bluetooth.manager.discovery_flow.async_create_flow",
        _create_flow,
    ):
        yield


def _service_info_from_capture(ad: dict) -> BluetoothServiceInfoBleak:
    """Build a real BluetoothServiceInfoBleak from a captured advertisement."""
    manufacturer_data = {
        int(mfg_id): bytes.fromhex(data)
        for mfg_id, data in ad["manufacturer_data"].items()
    }
    service_data = {
        uuid: bytes.fromhex(data) for uuid, data in ad["service_data"].items()
    }
    advertisement = AdvertisementData(
        local_name=ad["name"],
        manufacturer_data=manufacturer_data,
        service_data=service_data,
        service_uuids=ad["service_uuids"],
        tx_power=ad["tx_power"],
        rssi=ad["rssi"],
        platform_data=(),
    )
    return BluetoothServiceInfoBleak(
        name=ad["name"],
        address=ad["address"],
        rssi=ad["rssi"],
        manufacturer_data=manufacturer_data,
        service_data=service_data,
        service_uuids=ad["service_uuids"],
        source="local",
        device=BLEDevice(ad["address"], ad["name"], {}),
        advertisement=advertisement,
        connectable=ad["connectable"],
        time=time.monotonic(),
        tx_power=ad["tx_power"],
    )


def _load_capture() -> dict:
    """Return the first captured JHT advertisement."""
    ads = json.loads(
        (Path(__file__).parent / "test_ble_advertisements.json").read_text()
    )
    return ads[0]


async def _inject(hass: HomeAssistant, ad: dict) -> None:
    """Feed an advertisement to the bluetooth manager and let flows start."""
    get_manager().scanner_adv_received(_service_info_from_capture(ad))
    # Discovery flows are started as background tasks.
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_advertisement_starts_discovery_flow(hass: HomeAssistant) -> None:
    """Test a captured JHT advertisement starts a jaalee discovery flow."""
    await _inject(hass, _load_capture())

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_BLUETOOTH
    assert flows[0]["step_id"] == "bluetooth_confirm"


async def test_passive_advertisement_starts_discovery_flow(
    hass: HomeAssistant,
) -> None:
    """
    Test discovery without the scan response.

    The f525 service data is only sent in the scan response, which passive
    scanners (and AUTO-mode adapters outside an active window) never request,
    so discovery has to work from the iBeacon manufacturer data alone.
    """
    ad = _load_capture() | {"service_data": {}, "service_uuids": []}

    await _inject(hass, ad)

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["step_id"] == "bluetooth_confirm"


async def test_foreign_ibeacon_does_not_offer_discovery(hass: HomeAssistant) -> None:
    """Test an iBeacon without the Jaalee marker is not offered for setup."""
    ad = _load_capture() | {
        "address": "AA:BB:CC:DD:EE:FF",
        "manufacturer_data": {"76": "0215ebefd08370a247c89837e7b5634d000067e48d2ecb64"},
        "service_data": {},
        "service_uuids": [],
    }

    await _inject(hass, ad)

    assert hass.config_entries.flow.async_progress_by_handler(DOMAIN) == []
