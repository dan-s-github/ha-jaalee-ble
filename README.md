# Jaalee BLE

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

Home Assistant integration for Jaalee Bluetooth Low Energy (BLE) devices.

This integration automatically discovers and monitors Jaalee BLE sensors through passive Bluetooth scanning. It supports temperature, humidity, battery percentage, and signal strength (UID Tx power) diagnostics. Additional sensor types (CO2, voltage, light, pressure) are prepared for when supported by Jaalee devices. UV is planned for future parser support.

## Features

- **Automatic Discovery**: Automatically detects Jaalee BLE devices in range
- **Passive Scanning**: Uses Bluetooth passive scanning mode for efficient battery usage
- **Multiple Sensor Types**:
  - Temperature (°C)
  - Humidity (%)
  - Battery (%)
  - UID Tx Power (dBm, diagnostic)
- **No YAML Configuration Required**: Devices are discovered through Bluetooth and added with the UI flow

## Requirements

- Home Assistant 2025.12.0 or newer
- Bluetooth adapter (built-in or USB)
- Jaalee BLE device broadcasting iBeacon telemetry

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dan-s-github&repository=ha-jaalee-ble&category=Integration)

"Download" and Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the `custom_components/jaalee` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Jaalee BLE"
4. Select your Jaalee device from the list of discovered devices
5. Click **Submit**

The integration will automatically create sensor entities for:

- Temperature
- Humidity
- Battery

## Development (Devcontainer + Bluetooth)

- Run `scripts/setup` once after cloning. It installs dependencies and links `config/custom_components` to the repository `custom_components` directory.
- Start Home Assistant with `scripts/develop`.
- Optional direct command: `uv run --group dev hass --config config --debug`.
- Dependency policy: pin the Home Assistant version we target and rely on its dependency set for transitive packages; avoid manually pinning Home Assistant internals unless there is a documented compatibility break.
- For Python 3.13 development environments, keep `bluetooth-adapters>=2.1.0` and `habluetooth>=5.7.0` so Home Assistant Bluetooth imports stay compatible.
- Keep `pycares<5` in the dev dependency group for now; `aiodns` currently expects legacy `pycares.ares_query_*` types and can fail at import time with pycares 5.x.
- On macOS hosts, the VS Code devcontainer cannot map the host Bluetooth adapter for Home Assistant BLE testing.
- On Linux hosts, configure the devcontainer with `--network=host`, `--cap-add=NET_ADMIN`, and `--cap-add=NET_RAW`; these capabilities are required for Home Assistant Bluetooth adapter management and automatic adapter recovery.
- On Linux hosts, mount D-Bus (`/run/dbus`) into the devcontainer if you need full adapter introspection and control.
- On Linux hosts, Bluetooth passthrough may work with host networking/privileged mode and a D-Bus mount.
- If BLE discovery still does not work in-container, run Home Assistant directly on the host or test on a physical Linux machine.

## Supported Devices

This integration supports Jaalee BLE devices that broadcast iBeacon telemetry data with service data UUID `0000f525-0000-1000-8000-00805f9b34fb`.

## Troubleshooting

### Device Not Discovered

- Ensure your Jaalee device is powered on and in range
- Check that Bluetooth is enabled in Home Assistant
- Try restarting the Bluetooth adapter

### Sensors Not Updating

- Check the device battery level
- Ensure the device is within Bluetooth range
- Review Home Assistant logs for any error messages

### Bluetooth Recovery Warnings In Development

If you see warnings such as `Operation not permitted` from `bluetooth_auto_recovery.recover`, Home Assistant can usually still scan, but it cannot power-cycle the adapter for recovery.

- In a devcontainer, ensure `--network=host`, `--cap-add=NET_ADMIN`, and `--cap-add=NET_RAW` are active, then rebuild/reopen the container.
- Mount D-Bus (`/run/dbus`) into the container when testing Bluetooth recovery behavior.
- If you run Home Assistant directly on Linux host, run `sudo scripts/enable-bt-caps` once to grant Bluetooth management capabilities to the interpreter used by this project venv.
- To roll back host capability changes, run `sudo scripts/disable-bt-caps`.

If logs mention `passive scanning on Linux requires BlueZ >= 5.56 with --experimental enabled`, verify `bluetoothd` is started with `--experimental`.

- Check current service command: `systemctl show bluetooth -p ExecStart --value`
- If `--experimental` is missing, run `sudo systemctl edit bluetooth` and add:
  - `[Service]`
  - `ExecStart=`
  - `ExecStart=/usr/libexec/bluetooth/bluetoothd --experimental`
- Apply with `sudo systemctl daemon-reload && sudo systemctl restart bluetooth`

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Report a Bug][issues]
- [Request a Feature][issues]
- [Ask a Question][issues]

---

[releases-shield]: https://img.shields.io/github/release/dan-s-github/ha-jaalee-ble.svg?style=for-the-badge
[releases]: https://github.com/dan-s-github/ha-jaalee-ble/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/dan-s-github/ha-jaalee-ble.svg?style=for-the-badge
[commits]: https://github.com/dan-s-github/ha-jaalee-ble/commits/main
[license-shield]: https://img.shields.io/github/license/dan-s-github/ha-jaalee-ble.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[issues]: https://github.com/dan-s-github/ha-jaalee-ble/issues
