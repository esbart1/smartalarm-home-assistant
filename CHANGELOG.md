# Changelog

## 0.4.1

First GitHub release candidate based on the tested SmartAlarm development build.

- Alarm control: away, home and disarmed
- Persistent SmartAlarm event history
- Persistent per-device signal measurements and hourly history
- Manual signal calibration with 10 valid measurements and a 30-minute timeout
- Signal status, signal calibration state and signal diagnosis
- Configurable normal/warning signal thresholds
- Persistent device identity based on the SmartAlarm device ID
- SmartAlarm alarm panel and SmartAlarm fire-alarm panel
- Smoke, heat and CO device handling
- Dutch and English config-flow translations
- Protection against losing an existing signal calibration during cache errors or normal reloads
