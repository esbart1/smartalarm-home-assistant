# Changelog

# SmartAlarm 0.4.15 — releasecontrole

## Uitgangspunt

De releasekandidaat is gebaseerd op `smartalarm0.4.15.zip`, de versie die op de productie- en testinstallatie staat. De werkende alarmbediening en de alarm-/sabotagelogica zijn niet aangepast. De UTC-logaanpassing is niet opgenomen.

## Uitgevoerde controles

- `manifest.json` bevat versie `0.4.15`.
- Alle Python-bestanden zijn syntactisch parseerbaar.
- Alle JSON-bestanden zijn geldig.
- Er zitten geen `__pycache__`-mappen of `.pyc`-bestanden in de ZIP.
- Er is geen uitvoerbare hardcoded basisstation-ID gevonden; `1429` komt alleen voor in een voorbeeldcommentaar bij het uitlezen van HTML.
- Het basisstation-ID wordt eerst uit `/json/bases/me` gehaald, met een dashboardfallback.
- De alarmcentrale en apparaatidentificaties gebruiken het dynamische basisstation-ID.
- Eventhistorie en signaalkalibratie gebruiken Home Assistant `Store`-opslag.
- `event_store.py` en `services.yaml` ontbreken; er zijn geen verwijzingen gevonden naar `set_signal_test` of `EVENT_CACHE_MAX`.
- De kandidaat met tekstverbeteringen wijzigt alleen `strings.json`, `translations/en.json` en `translations/nl.json`; Python-code is identiek aan de aangeleverde ZIP.
- De nieuwe vertalingen bevatten de configuratiestap `reauth_confirm`, de melding `invalid_auth` en de afsluitreden `reauth_successful`, passend bij de bestaande configuratiecode.

## Wat nog niet door deze controle bewezen is

- Een echte SmartAlarm-login is niet opnieuw uitgevoerd in deze controle; de praktijkproeven op productie en test blijven de bestaande testbewijzen.
- Een mislukte login of verlopen sessie is niet live gesimuleerd in een Home Assistant-testomgeving.
- HACS Action en Hassfest moeten tegen de definitieve commit/releasebron opnieuw groen zijn.
- De GitHub-README en CHANGELOG zijn online nog niet bijgewerkt. De publieke README toont nog 0.4.11 en bevat een verouderde omschrijving van de cachelocatie.

## Aanbevolen README-informatie

### Inloggen en opnieuw inloggen

Voeg SmartAlarm toe via Instellingen → Apparaten en diensten → Integratie toevoegen → SmartAlarm. Gebruik het e-mailadres en wachtwoord van een SmartAlarm-account dat toegang heeft tot de alarmcentrale.

De integratie meldt zich aan via de SmartAlarm-webomgeving en gebruikt de verkregen sessie voor status-, gebeurtenis- en apparaatgegevens en voor de bediening van het alarmsysteem. Als SmartAlarm de sessie niet meer accepteert, probeert de integratie opnieuw in te loggen. Als SmartAlarm de opgeslagen inloggegevens afwijst, kan Home Assistant vragen om opnieuw in te loggen via de integratie.

Het basisstation-ID wordt uit de accountgegevens opgehaald; de gebruiker hoeft dit niet zelf in te voeren.

### Teststatus

Versie 0.4.15 is door de ontwikkelaar getest met drie verschillende SmartAlarm-gebruikersaccounts en wachtwoorden. Ook zijn twee Home Assistant-installaties getest die hetzelfde basisstation gebruiken met verschillende accounts. Op beide installaties zijn herstarts en het in- en uitschakelen van het alarm getest. Dit beschrijft de daadwerkelijk geteste accounts en configuraties; niet iedere mogelijke accountconfiguratie is getest.

### Opslag

De integratie bewaart relevante gebeurtenishistorie en signaalkalibratie met de opslagvoorziening van Home Assistant (`Store`). Deze gegevens worden niet meer in de integratiemap opgeslagen en horen bij normale HACS-updates behouden te blijven.

## Changelog-kandidaat 0.4.15

- Voorkomen dat lage-batterijmeldingen als brand- of CO-alarm worden geïnterpreteerd.
- Brand-, CO- en sabotagestatus afzonderlijk per melder verwerken en ondersteunde herstelmeldingen afhandelen.
- Het basisstation-ID dynamisch uit de aangemelde SmartAlarm-accountgegevens ophalen in plaats van een vast ID te gebruiken.
- Afgewezen inloggegevens via Home Assistant-herauthenticatie afhandelen.
- Gebeurtenishistorie en signaalkalibratie opslaan via Home Assistant `Store`.
- Ongebruikte integratiecode en niet-geregistreerde serviceverwijzingen verwijderen.
- Getest met drie SmartAlarm-accounts en twee Home Assistant-installaties met afzonderlijke accounts op hetzelfde basisstation.

Controleer de changelog nog tegen de definitieve broncode voordat de release wordt gepubliceerd.


All notable changes to this project are documented in this file.

## 0.4.11

### Changed
- Updated SmartAlarm device linking to use the current Home Assistant device registry approach for fire-related devices.
- Improved compatibility with current Home Assistant entity and device handling.
- Updated integration setup to address blocking platform-import warnings.

### Fixed
- Fixed an indentation issue in `binary_sensor.py` that prevented the integration from loading correctly.
- Improved the handling of individual SmartAlarm device entities and their association with the fire-alarm panel.

### Testing
- Verified that Home Assistant starts successfully after correcting the binary sensor indentation.
- Verified that smoke and CO sensors appear in Home Assistant.
- Verified the integration with the local Home Assistant installation.

## 0.4.9 

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

## 0.4.7

Small UI and entity-behavior fixes.

- The normal signal threshold uses the same reliable signal icon as the signal-strength entity.
- Binary sensor device classes are assigned before entity registration, so movement sensors use the correct Home Assistant motion semantics and display states accordingly.
- The existing event-cache implementation remains in `coordinator.py`; the older standalone `event_store.py` design is no longer used.

## 0.4.6

Cosmetic branding update.

- Added a custom SmartAlarm integration icon under `custom_components/smartalarm/brand/icon.png`.
- Added a Dutch integration description to the README.

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
