"""Test the Jaalee BLE config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jaalee.const import DOMAIN

from . import JAALEE_SERVICE_INFO, NOT_JAALEE_SERVICE_INFO


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Allow known bluetooth manager timer during config flow tests."""
    return True


async def test_async_step_bluetooth_valid_device(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JAALEE_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch("custom_components.jaalee.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {}
    assert result2["result"].unique_id == "FE:0E:A2:CC:C4:1F"


async def test_async_step_bluetooth_not_jaalee(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with unsupported advertisement."""
    with patch(
        "custom_components.jaalee.config_flow.DeviceData.supported",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=NOT_JAALEE_SERVICE_INFO,
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_async_step_user_no_devices_found(hass: HomeAssistant) -> None:
    """Test user flow aborts when no devices are discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_with_found_devices(hass: HomeAssistant) -> None:
    """Test setup from discovery cache with supported devices found."""
    with patch(
        "custom_components.jaalee.config_flow.async_discovered_service_info",
        return_value=[JAALEE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch("custom_components.jaalee.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "FE:0E:A2:CC:C4:1F"},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {}
    assert result2["result"].unique_id == "FE:0E:A2:CC:C4:1F"


async def test_async_step_user_device_added_between_steps(hass: HomeAssistant) -> None:
    """Test device becomes configured between user step form and submit."""
    with patch(
        "custom_components.jaalee.config_flow.async_discovered_service_info",
        return_value=[JAALEE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    with patch("custom_components.jaalee.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "FE:0E:A2:CC:C4:1F"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_async_step_user_with_found_devices_already_setup(
    hass: HomeAssistant,
) -> None:
    """Test user flow ignores devices that are already configured."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    with patch(
        "custom_components.jaalee.config_flow.async_discovered_service_info",
        return_value=[JAALEE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_bluetooth_devices_already_setup(hass: HomeAssistant) -> None:
    """Test bluetooth flow aborts when device already has config entry."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="FE:0E:A2:CC:C4:1F")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JAALEE_SERVICE_INFO,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_bluetooth_already_in_progress(hass: HomeAssistant) -> None:
    """Test duplicate bluetooth discovery creates already_in_progress abort."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JAALEE_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JAALEE_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_in_progress"


async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual user flow can complete while discovery flow is pending."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JAALEE_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "custom_components.jaalee.config_flow.async_discovered_service_info",
        return_value=[JAALEE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM

    with patch("custom_components.jaalee.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "FE:0E:A2:CC:C4:1F"},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {}
    assert result2["result"].unique_id == "FE:0E:A2:CC:C4:1F"

    assert not hass.config_entries.flow.async_progress(DOMAIN)
