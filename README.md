# SmartAlarm Home Assistant integration

Custom Home Assistant integration for SmartAlarm.

The integration connects to the SmartAlarm cloud service and provides alarm control, event history, device states, signal strength monitoring, signal diagnostics, and the SmartAlarm fire-alarm panel.

## Current status

This repository contains the tested development version that was built incrementally in Home Assistant.

Included functionality:

- Alarm states: away, home, disarmed
- Persistent SmartAlarm event history
- Persistent per-device signal measurements and history
- Manual signal calibration with a 30-minute safety timeout
- Signal status and signal diagnosis
- Configurable normal/warning signal thresholds
- SmartAlarm device identity based on the SmartAlarm device ID
- SmartAlarm alarm panel and fire-alarm panel
- Smoke, heat and CO device handling
- Dutch translations

## Installation

### HACS

This repository can be added to HACS as a custom repository while it is not yet part of the HACS default catalog.

Repository:

`https://github.com/esbart1/smartalarm-home-assistant`

Type: `Integration`

### Manual

Copy the `custom_components/smartalarm` directory to:

`/config/custom_components/smartalarm`

Restart Home Assistant and add **SmartAlarm** through the integration setup screen.

## Important data handling

The integration stores its persistent event and signal history in Home Assistant's `custom_components/smartalarm/alarm_cache` directory. That runtime cache is intentionally excluded from the Git repository.

`__pycache__`, Python bytecode, runtime cache data, local logs and generated ZIP files are also excluded from Git.

## Support

Please use the GitHub Issues section for bug reports and feature requests.

## Disclaimer

SmartAlarm is a third-party service. This project is an independent community integration and is not an official SmartAlarm or Home Assistant product.
