# Changelog

All notable changes to this project are documented in this file.

## 0.4.9 - Release candidate

### Added
- Added improved event storage and recovery handling.
- Added Home Assistant service definitions and translations.
- Added support for retaining relevant recent SmartAlarm events after a restart.

### Changed
- Improved synchronization of individual binary sensors with the current SmartAlarm device status.
- Current live SmartAlarm device status now takes priority over cached event information.
- Cached event information is used as a startup fallback until current device status is available.
- Motion sensors now return to `off` automatically after a short detection period.
- Motion events are no longer stored in the persistent event cache.
- Event cache size is limited to 200 relevant events.
- Improved alarm-panel and event message formatting.
- Improved sensor and entity creation.
- Updated integration metadata for version 0.4.9.

### Fixed
- Fixed individual door/window binary sensors not always reflecting the latest SmartAlarm status.
- Fixed motion sensors remaining active after a motion event or restart.
- Fixed cached event information being able to override the current device state.
- Fixed inconsistent event information after Home Assistant restarts.

### Testing
- Tested from a clean installation directly from the GitHub `test-0.4.9` branch.
- Verified alarm panel and individual sensor creation.
- Verified 12 SmartAlarm devices/panels and 105 Home Assistant entities in the test installation.
- Verified door/window state changes.
- Verified motion reset behavior.
- Verified motion events are excluded from the persistent event cache.
- Verified state recovery after restart.
- Verified state changes occurring around a restart.
