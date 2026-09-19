# Changelog

## 0.4.5

Compact event-cache and state-restoration update.

- Ordinary motion and door/window state events are no longer persisted in `smartalarm_events.json`.
- Security-relevant alarm, intrusion, tamper, fire and CO events remain persisted.
- The event cache is limited to 200 significant events.
- Old non-significant events are pruned from the cache on a successful load.
- The intrusion binary sensor and door/window binary sensors can restore their last known Home Assistant state while current SmartAlarm data is not yet available.
- The last-event sensor no longer duplicates the complete event cache in its state attributes.

## 0.4.4

Signal threshold sliders are shown as normal device controls, matching the v40 layout, while remaining adjustable percentage sliders.

## 0.4.3

Test build that moves the per-device signal threshold settings from read-only sensors to configurable Home Assistant number entities with sliders.

- `Signaalgrens normaal` is now an adjustable percentage of the calibrated reference.
- `Signaalgrens waarschuwing` is now an adjustable percentage of the calibrated reference.
- The calculated threshold in dB remains available as an entity attribute.
- The existing calibration and threshold storage in `smartalarm_signal.json` is preserved.

## 0.4.2

Test release following the first clean GitHub installation.

- Restored the working SmartAlarm alarm control panel with away, home and disarm controls and the correct alarm-panel device.
- Restored the SmartAlarm control-panel device discovery from the authenticated device inventory.
- Restored the two per-device signal threshold entities: normal and warning.
- Smoke and CO alarm detection now follows explicit fire/CO alarm events instead of generic `open`/`on` device states.
- Smoke, heat and CO entities remain linked to the SmartAlarm fire-alarm panel.
- Improved authenticated HTML device-page parsing of signal values.
- Kept persistent calibration protection and event/signal history handling from 0.4.1.

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
