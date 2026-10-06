# SmartAlarm Home Assistant

A Home Assistant custom integration for **SmartAlarm** systems.

This integration connects SmartAlarm directly to Home Assistant and exposes the alarm panel and individual SmartAlarm devices as Home Assistant entities.

## Features

- Alarm panel with the SmartAlarm alarm status.
- Individual door and window contact sensors.
- Motion sensors.
- Smoke and heat detectors.
- Battery/status information where provided by SmartAlarm.
- Event messages shown in Home Assistant.
- Sensor states are updated from the current SmartAlarm device status.
- Recent event information is retained so useful information can be restored after a Home Assistant restart.
- Motion events are treated as temporary events and are not stored in the event cache.
- Up to 200 relevant recent events are retained in the local event cache.
- The integration creates the SmartAlarm devices and their associated entities automatically.

## Version 0.4.9

Version 0.4.9 focuses on reliable sensor state handling and event recovery.

### Important changes

- Improved synchronization of individual binary sensors with the current SmartAlarm device status.
- Current SmartAlarm status takes priority over cached event information.
- Cached event information is used as a fallback during startup when the current device status has not arrived yet.
- Motion sensors automatically return to `off` after a short detection period.
- Motion events are no longer written to the persistent event cache.
- Relevant event history is limited to 200 entries.
- Improved event and alarm-panel message formatting.
- Improved handling of event information after a Home Assistant restart.
- Added/updated Home Assistant service definitions and translations.
- Improved sensor and alarm-panel entity creation.

## Installation

### HACS

The recommended installation method is **HACS**.

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. Search for **SmartAlarm**.
4. Install the integration.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services**.
7. Add **SmartAlarm** and enter the required SmartAlarm account details.

If SmartAlarm is not yet available in the HACS default repository, the repository can be added as a custom repository in HACS.

### Manual installation

1. Download the latest release from GitHub.
2. Copy the `custom_components/smartalarm` directory into:

```text
/config/custom_components/
```

The final structure should be:

```text
/config/custom_components/smartalarm/
```

3. Restart Home Assistant.
4. Add SmartAlarm through **Settings → Devices & services**.

## Entities

The integration creates the SmartAlarm alarm panel and individual SmartAlarm devices as Home Assistant entities.

Depending on the devices configured in your SmartAlarm system, this can include:

- Door/window contacts
- Motion detectors
- Smoke detectors
- Heat detectors
- Battery/status sensors
- Alarm status
- Event information

The exact number of entities depends on the SmartAlarm installation.

## Event cache

The integration keeps a small local cache of relevant SmartAlarm events.

The cache is intended primarily to make recent event information available again after a Home Assistant restart. It is **not intended as a replacement for Home Assistant's own recorder/history**.

Motion events are deliberately excluded because motion is a short-lived state and should be represented by the Home Assistant entity state and history instead.

The cache is limited to the most recent 200 relevant events.

## Sensor state after restart

After a Home Assistant restart, cached event information can temporarily provide the last known state while SmartAlarm is reconnecting.

As soon as the current SmartAlarm device status is available, that live status takes priority over the cached information.

This prevents an old cached event from permanently overriding the actual current state of a door, window, or other device.

## Troubleshooting

If the integration does not appear after installation:

1. Confirm that the integration is located in:

```text
/config/custom_components/smartalarm/
```

2. Restart Home Assistant.
3. Check **Settings → Devices & services**.
4. Check the Home Assistant logs for SmartAlarm errors.

If a sensor state appears incorrect after a restart, allow the SmartAlarm connection a moment to synchronize. The current SmartAlarm device status should replace any temporary cached state.

## Development and testing

The `test-0.4.9` branch is used for testing before an official release.

The production installation should use an official release once the version has completed testing.

## Disclaimer

This is a community-developed Home Assistant integration and is not an official SmartAlarm product.

Use it at your own risk. SmartAlarm API behavior or availability may change without notice.

## License

See the repository for the applicable license and project information.
