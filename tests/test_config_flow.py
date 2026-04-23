"""Test config flow for jaalee integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS

from custom_components.jaalee.config_flow import JaaleeConfigFlow


@pytest.fixture
def config_flow() -> JaaleeConfigFlow:
    """Create a config flow instance."""
    return JaaleeConfigFlow()


@pytest.fixture
def mock_discovery_info() -> MagicMock:
    """Create mock discovery info."""
    info = MagicMock(spec=BluetoothServiceInfoBleak)
    info.address = "AA:BB:CC:DD:EE:FF"
    info.name = "Jaalee Device"
    return info


@pytest.fixture
def mock_device_data() -> MagicMock:
    """Create mock device data."""
    device = MagicMock()
    device.title = "Test Jaalee Device"
    device.get_device_name.return_value = "Test Device"
    device.supported.return_value = True
    return device


def test_config_flow_version(config_flow) -> None:
    """Test that config flow version is set correctly."""
    assert config_flow.VERSION == 1


def test_config_flow_initialization(config_flow) -> None:
    """Test config flow initialization."""
    assert config_flow._discovery_info is None  # noqa: SLF001
    assert config_flow._discovered_device is None  # noqa: SLF001
    assert config_flow._discovered_devices == {}  # noqa: SLF001


@pytest.mark.asyncio
async def test_async_step_bluetooth_supported_device(
    config_flow: JaaleeConfigFlow,
    mock_discovery_info: MagicMock,
    mock_device_data: MagicMock,
) -> None:
    """Test bluetooth discovery step with supported device."""
    config_flow.hass = MagicMock()
    config_flow.async_set_unique_id = AsyncMock()
    config_flow._abort_if_unique_id_configured = MagicMock()  # noqa: SLF001

    with patch(
        "custom_components.jaalee.config_flow.DeviceData", return_value=mock_device_data
    ):
        config_flow.async_step_bluetooth_confirm = AsyncMock(
            return_value={"type": "form"}
        )

        await config_flow.async_step_bluetooth(mock_discovery_info)

        # Verify unique ID was set
        config_flow.async_set_unique_id.assert_called_once_with(
            mock_discovery_info.address
        )
        # Verify abort if already configured was called
        config_flow._abort_if_unique_id_configured.assert_called_once()  # noqa: SLF001
        # Verify device info was stored
        assert config_flow._discovery_info == mock_discovery_info  # noqa: SLF001
        assert config_flow._discovered_device == mock_device_data  # noqa: SLF001
        # Verify next step was called
        config_flow.async_step_bluetooth_confirm.assert_called_once()


@pytest.mark.asyncio
async def test_async_step_bluetooth_unsupported_device(
    config_flow: JaaleeConfigFlow, mock_discovery_info: MagicMock
) -> None:
    """Test bluetooth discovery step with unsupported device."""
    config_flow.hass = MagicMock()
    config_flow.async_set_unique_id = AsyncMock()
    config_flow._abort_if_unique_id_configured = MagicMock()  # noqa: SLF001
    config_flow.async_abort = MagicMock(return_value={"type": "abort"})

    mock_device_data = MagicMock()
    mock_device_data.supported.return_value = False

    with patch(
        "custom_components.jaalee.config_flow.DeviceData", return_value=mock_device_data
    ):
        await config_flow.async_step_bluetooth(mock_discovery_info)

        config_flow.async_abort.assert_called_once_with(reason="not_supported")


@pytest.mark.asyncio
async def test_async_step_bluetooth_confirm_with_user_input(
    config_flow: JaaleeConfigFlow,
    mock_discovery_info: MagicMock,
    mock_device_data: MagicMock,
) -> None:
    """Test bluetooth confirm step with user input."""
    config_flow._discovered_device = mock_device_data  # noqa: SLF001
    config_flow._discovery_info = mock_discovery_info  # noqa: SLF001
    config_flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

    await config_flow.async_step_bluetooth_confirm(user_input={})

    config_flow.async_create_entry.assert_called_once()
    call_args = config_flow.async_create_entry.call_args
    assert "title" in call_args.kwargs


@pytest.mark.asyncio
async def test_async_step_bluetooth_confirm_show_form(
    config_flow: JaaleeConfigFlow,
    mock_discovery_info: MagicMock,
    mock_device_data: MagicMock,
) -> None:
    """Test bluetooth confirm step shows form without user input."""
    config_flow._discovered_device = mock_device_data  # noqa: SLF001
    config_flow._discovery_info = mock_discovery_info  # noqa: SLF001
    config_flow._set_confirm_only = MagicMock()  # noqa: SLF001
    config_flow.async_show_form = MagicMock(return_value={"type": "form"})
    config_flow.context = {}

    await config_flow.async_step_bluetooth_confirm(user_input=None)

    config_flow._set_confirm_only.assert_called_once()  # noqa: SLF001
    config_flow.async_show_form.assert_called_once()


@pytest.mark.asyncio
async def test_async_step_bluetooth_confirm_missing_device(config_flow) -> None:
    """Test bluetooth confirm step with missing device info."""
    config_flow._discovered_device = None  # noqa: SLF001
    config_flow._discovery_info = None  # noqa: SLF001
    config_flow.async_abort = MagicMock(return_value={"type": "abort"})

    await config_flow.async_step_bluetooth_confirm()

    config_flow.async_abort.assert_called_once_with(reason="not_supported")


@pytest.mark.asyncio
async def test_async_step_user_with_selection(
    config_flow: JaaleeConfigFlow,
) -> None:
    """Test user step with device selection."""
    config_flow.async_set_unique_id = AsyncMock()
    config_flow._abort_if_unique_id_configured = MagicMock()  # noqa: SLF001
    config_flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    config_flow._async_current_ids = MagicMock(return_value=set())  # noqa: SLF001
    config_flow._discovered_devices = {  # noqa: SLF001
        "AA:BB:CC:DD:EE:FF": "Test Device"
    }

    await config_flow.async_step_user(user_input={CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"})

    config_flow.async_set_unique_id.assert_called_once_with(
        "AA:BB:CC:DD:EE:FF", raise_on_progress=False
    )
    config_flow._abort_if_unique_id_configured.assert_called_once()  # noqa: SLF001
    config_flow.async_create_entry.assert_called_once()


@pytest.mark.asyncio
async def test_async_step_user_no_devices(config_flow: JaaleeConfigFlow) -> None:
    """Test user step when no devices are discovered."""
    config_flow.hass = MagicMock()
    config_flow._async_current_ids = MagicMock(return_value=set())  # noqa: SLF001
    config_flow.async_abort = MagicMock(return_value={"type": "abort"})

    with (
        patch(
            "custom_components.jaalee.config_flow.async_discovered_service_info",
            return_value=[],
        ),
        patch("custom_components.jaalee.config_flow.DeviceData"),
    ):
        await config_flow.async_step_user()

        config_flow.async_abort.assert_called_once_with(reason="no_devices_found")
