# SmartAlarm Home Assistant integration

Nederlandse Home Assistant-integratie voor SmartAlarm.

Met deze integratie kun je het SmartAlarm-alarmsysteem rechtstreeks vanuit Home Assistant bedienen. De alarmcentrale kan vanuit Home Assistant in de standen **aan**, **thuis** en **uit** worden gezet.

Daarnaast worden de afzonderlijke SmartAlarm-apparaten als losse Home Assistant-entiteiten aangeboden. De deur-, raam- en bewegingsmelders kunnen daardoor rechtstreeks worden gebruikt in **Home Assistant-automatiseringen**, meldingen en andere logica. Ook zijn onder meer inbraak-, sabotage-, brand- en CO-meldingen beschikbaar.

## Nederlandse beschrijving

Waarom deze integratie?

SmartAlarm is een Nederlands alarmsysteem. Ik heb deze integratie oorspronkelijk ontwikkeld omdat ik mijn eigen SmartAlarm-systeem uitgebreider wilde kunnen gebruiken in Home Assistant.

Er zijn andere mogelijkheden om SmartAlarm met Home Assistant te koppelen, bijvoorbeeld via IFTTT, IMAP of Olisto. In de praktijk kan dit echter omslachtig zijn. Ook zijn er mogelijkheden waarbij vooral de alarmstatus beschikbaar is, terwijl de afzonderlijke SmartAlarm-sensoren niet rechtstreeks in Home Assistant kunnen worden gebruikt.

Deze integratie maakt juist de afzonderlijke SmartAlarm-apparaten en sensoren rechtstreeks beschikbaar in Home Assistant. Hierdoor kunnen onder andere deur- en raamcontacten, bewegingsmelders en rook-, hitte- en CO-melders afzonderlijk worden gebruikt in automatiseringen, meldingen en andere Home Assistant-logica.

Ik heb de integratie eerst voor mijn eigen installatie ontwikkeld en uitgebreid getest. Nu deze goed werkt, stel ik hem beschikbaar voor andere SmartAlarm-gebruikers die hun systeem met Home Assistant willen gebruiken.

**SmartAlarm voor Home Assistant** is een onafhankelijke integratie voor het Nederlandse SmartAlarm-platform. De integratie haalt de actuele alarmstatus en apparaatgegevens uit SmartAlarm en maakt deze beschikbaar in Home Assistant.

Naast de bediening van de alarmcentrale biedt de integratie per ondersteund apparaat onder meer:
- de actuele signaalsterkte;
- signaalstatus en signaaldiagnose;
- een eigen handmatige signaalkalibratie;
- instelbare signaalgrenzen;
- de afzonderlijke sensorstatus, zodat de sensoren in Home Assistant-automatiseringen kunnen worden gebruikt.

### Waarom iedere sensor afzonderlijk kalibreren?

Iedere SmartAlarm-sensor heeft zijn eigen positie, afstand, bouwmaterialen en lokale omstandigheden. Daarom wordt iedere sensor **afzonderlijk gekalibreerd**. Tijdens een handmatige kalibratie worden geldige metingen verzameld en wordt voor die specifieke sensor een eigen **referentiewaarde** vastgesteld.

Die referentiewaarde is de persoonlijke nulmeting van de sensor: niet een absolute RSSI-waarde van 0 dB, maar het normale ontvangstniveau van die sensor op zijn eigen locatie. Vanaf die eigen referentie kan Home Assistant bepalen of de ontvangst normaal is, lager dan normaal of sterk verzwakt. Daardoor kan het systeem per sensor signaleren wanneer de ontvangstkwaliteit duidelijk afwijkt van de gebruikelijke situatie.


The integration connects to the SmartAlarm cloud service and provides alarm control, event history, device states, signal strength monitoring, signal diagnostics, and a logical SmartAlarm fire-alarm status.





A Home Assistant custom integration for **SmartAlarm** systems.

This integration connects SmartAlarm directly to Home Assistant and exposes the alarm panel and individual SmartAlarm devices as Home Assistant entities.


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
