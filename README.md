# SmartAlarm Home Assistant integration

Custom Home Assistant integration for SmartAlarm.

The integration connects to the SmartAlarm cloud service and provides alarm control, event history, device states, signal strength monitoring, signal diagnostics, and a logical SmartAlarm fire-alarm status.

## Current status

Version **0.4.5** is the current test build. The signal thresholds are now configurable Home Assistant number entities with sliders.

Included functionality:

- Alarm states: away, home, disarmed
- Persistent SmartAlarm event history
- Persistent per-device signal measurements and hourly history
- Manual signal calibration with 10 valid measurements and a 30-minute safety timeout
- Signal status and signal diagnosis
- Normal and warning signal thresholds per device
- SmartAlarm device identity based on the SmartAlarm device ID
- SmartAlarm alarm control panel
- SmartAlarm fire-alarm status for smoke, heat and CO devices
- Smoke, heat and CO device handling
- Dutch and English config-flow translations

## Installation

### HACS

The repository can be added to HACS as a custom repository while it is not yet part of the HACS default catalog.

Repository:

`https://github.com/esbart1/smartalarm-home-assistant`

Type: `Integration`

### Manual

Copy the `custom_components/smartalarm` directory to:

`/config/custom_components/smartalarm`

Restart Home Assistant and add **SmartAlarm** through the integration setup screen.

## Important data handling

The integration stores persistent signal calibration/history and a compact security-relevant event cache in Home Assistant's `custom_components/smartalarm/alarm_cache` directory. Ordinary motion and door/window state history is left to Home Assistant Recorder. The runtime cache is intentionally excluded from the Git repository.

`__pycache__`, Python bytecode, runtime cache data, local logs and generated ZIP files are also excluded from Git.

## Support

Please use the GitHub Issues section for bug reports and feature requests.

## Disclaimer

SmartAlarm is a third-party service. This project is an independent community integration and is not an official SmartAlarm or Home Assistant product.
