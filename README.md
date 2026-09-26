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

## Current status

Version **0.4.7** is the current test build. The signal thresholds are now configurable Home Assistant number entities with sliders.

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
