# SmartAlarm Home Assistant Integration

**Current version: 0.4.11**

[🇳🇱 Nederlands](#nederlands) | [🇬🇧 English](#english)

An independent community integration for connecting your SmartAlarm security system to Home Assistant.

---

<a name="nederlands"></a>
## 🇳🇱 Nederlands

Met deze integratie kun je het SmartAlarm-alarmsysteem rechtstreeks vanuit Home Assistant bedienen. De alarmcentrale kan in de standen **aan**, **thuis** en **uit** worden gezet.

Daarnaast worden afzonderlijke SmartAlarm-apparaten als Home Assistant-entiteiten aangeboden. Hierdoor kun je deur-, raam- en bewegingsmelders en andere ondersteunde sensoren rechtstreeks gebruiken in automatiseringen, meldingen en andere Home Assistant-logica.

### Waarom deze integratie?

SmartAlarm is een Nederlands alarmsysteem. Ik heb deze integratie oorspronkelijk ontwikkeld omdat ik mijn eigen SmartAlarm-systeem uitgebreider wilde kunnen gebruiken in Home Assistant.

Er zijn andere manieren om SmartAlarm te koppelen, bijvoorbeeld via IFTTT, IMAP of Olisto. Deze oplossingen kunnen omslachtig zijn of bieden niet altijd directe toegang tot de afzonderlijke sensoren.

Deze integratie richt zich juist op het rechtstreeks beschikbaar maken van de alarmcentrale en individuele SmartAlarm-apparaten in Home Assistant.

Ik heb de integratie eerst voor mijn eigen installatie ontwikkeld en getest. Nu stel ik deze beschikbaar voor andere SmartAlarm-gebruikers.

### Functionaliteit

Afhankelijk van de apparaten in je installatie biedt de integratie onder meer:

- Bediening van de alarmcentrale: aan, thuis en uit.
- Afzonderlijke entiteiten voor ondersteunde SmartAlarm-apparaten.
- Statussen van deur-, raam- en bewegingsmelders.
- Ondersteuning voor rook-, hitte- en CO-melders.
- Inbraak-, sabotage-, brand- en CO-gerelateerde meldingen, voor zover beschikbaar via SmartAlarm.
- Signaalsterkte en signaaldiagnose.
- Handmatige signaalkalibratie per sensor.
- Instelbare signaalgrenzen.
- Een logische brandalarmstatus.
- Lokale opslag van relevante recente gebeurtenissen.

### Signaalsterkte en kalibratie

Iedere SmartAlarm-sensor heeft een eigen positie, afstand, bouwmaterialen en lokale omstandigheden. Daarom kan de normale signaalsterkte per sensor verschillen.

Om die reden kan iedere sensor **afzonderlijk worden gekalibreerd**. Tijdens een handmatige kalibratie worden geldige metingen verzameld en wordt voor die sensor een eigen referentiewaarde vastgesteld.

Deze referentiewaarde is de persoonlijke nulmeting van de sensor. Het is geen absolute RSSI-waarde van 0 dB, maar het normale ontvangstniveau op de locatie van die sensor.

Aan de hand van deze referentie kan Home Assistant signaleren wanneer de ontvangst normaal is, lager dan normaal of sterk verzwakt. Hierdoor kunnen afwijkingen in de signaalkwaliteit per sensor worden gevolgd.

### Installatie via HACS

Versie **0.4.10** is voorbereid voor installatie via HACS. Versie **0.4.11** bouwt daarop voort.

1. Open HACS in Home Assistant.
2. Ga naar **Integraties**.
3. Zoek naar **SmartAlarm**.
4. Installeer de beschikbare versie.
5. Herstart Home Assistant.
6. Ga naar **Instellingen → Apparaten en diensten**.
7. Voeg SmartAlarm toe en vul je SmartAlarm-accountgegevens in.

Als de integratie niet in de HACS-standaardlijst staat, voeg dan eerst de GitHub-repository toe als aangepaste repository.

### Handmatige installatie

1. Download de gewenste versie van GitHub.
2. Kopieer de map `custom_components/smartalarm` naar:

   `/config/custom_components/`

3. Controleer of de uiteindelijke mapstructuur als volgt is:

   `/config/custom_components/smartalarm/`

4. Herstart Home Assistant.
5. Voeg SmartAlarm toe via **Instellingen → Apparaten en diensten**.

### Eventcache

De integratie bewaart lokaal een beperkte cache van relevante SmartAlarm-gebeurtenissen. Deze helpt om recente gebeurtenisinformatie na een herstart beschikbaar te houden.

De cache is beperkt tot de **200 meest recente relevante gebeurtenissen** en is geen vervanging voor de recorder- of geschiedenisfunctie van Home Assistant.

Bewegingsgebeurtenissen worden niet in deze permanente eventcache opgeslagen, omdat beweging een kortdurende toestand is die via de sensorentiteit en de Home Assistant-geschiedenis moet worden weergegeven.

### Sensorstatus na een herstart

Na een herstart kan opgeslagen gebeurtenisinformatie tijdelijk de laatst bekende status leveren terwijl SmartAlarm opnieuw verbinding maakt.

Zodra de actuele apparaatstatus beschikbaar is, krijgt deze voorrang op de opgeslagen informatie. Zo voorkomt de integratie dat een oude gebeurtenis de actuele status van een deur, raam of andere sensor blijft overschrijven.

### Problemen oplossen

Als de integratie niet verschijnt:

1. Controleer of de bestanden in `/config/custom_components/smartalarm/` staan.
2. Herstart Home Assistant.
3. Controleer **Instellingen → Apparaten en diensten**.
4. Bekijk de Home Assistant-logboeken op SmartAlarm-fouten.

Als een sensor na een herstart een onjuiste status toont, wacht dan even totdat de verbinding met SmartAlarm de actuele apparaatstatus heeft bijgewerkt.

### Ontwikkeling en testen

De integratie wordt verder ontwikkeld en getest voordat wijzigingen als officiële versie worden uitgebracht. Gebruik bij voorkeur een officiële release voor je productie-installatie.

### Disclaimer

Dit is een onafhankelijk door de community ontwikkelde Home Assistant-integratie. Het is geen officieel product van SmartAlarm.

Gebruik is op eigen risico. De beschikbaarheid of werking van de SmartAlarm API kan zonder voorafgaande kennisgeving veranderen.

### Licentie

Raadpleeg de repository voor de toepasselijke licentie en projectinformatie.

---

<a name="english"></a>
## 🇬🇧 English

This integration connects your SmartAlarm security system directly to Home Assistant. You can control the alarm panel using the **armed**, **home** and **disarmed** modes.

Individual supported SmartAlarm devices are also exposed as Home Assistant entities. This allows door, window and motion sensors, along with other supported devices, to be used directly in automations, notifications and other Home Assistant workflows.

### Why this integration?

SmartAlarm is a Dutch security system. I originally developed this integration because I wanted to make better use of my own SmartAlarm system in Home Assistant.

Other integration methods are available, including IFTTT, IMAP and Olisto. However, these approaches can be cumbersome or may not provide direct access to individual sensors.

This integration focuses on exposing the alarm panel and individual SmartAlarm devices directly in Home Assistant.

I initially developed and tested the integration with my own installation. I am now making it available to other SmartAlarm users.

### Features

Depending on the devices in your installation, the integration provides:

- Alarm panel control: armed, home and disarmed.
- Individual entities for supported SmartAlarm devices.
- Door, window and motion sensor states.
- Support for smoke, heat and CO detectors.
- Burglary, tamper, fire and CO-related notifications, where provided by SmartAlarm.
- Signal strength monitoring and diagnostics.
- Manual signal calibration for each sensor.
- Configurable signal thresholds.
- A logical fire-alarm status.
- Local storage of relevant recent events.

### Signal strength and calibration

Each SmartAlarm sensor has its own location, distance, building materials and environmental conditions. As a result, normal signal strength can vary between sensors.

For this reason, each sensor can be **calibrated individually**. During manual calibration, valid measurements are collected to establish a reference value for that specific sensor.

This reference value is the sensor's own baseline. It is not an absolute RSSI value of 0 dB; it represents the normal reception level at that sensor's location.

Home Assistant can use this baseline to identify whether reception is normal, below its usual level or significantly weakened. This makes it possible to monitor changes in signal quality for each sensor individually.

### Installation via HACS

Version **0.4.10** was prepared for HACS installation. Version **0.4.11** builds on that version.

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. Search for **SmartAlarm**.
4. Install the available version.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services**.
7. Add SmartAlarm and enter your SmartAlarm account credentials.

If the integration is not listed in the default HACS repository, add the GitHub repository as a custom repository first.

### Manual installation

1. Download the desired version from GitHub.
2. Copy the `custom_components/smartalarm` directory to:

   `/config/custom_components/`

3. Verify that the final directory structure is:

   `/config/custom_components/smartalarm/`

4. Restart Home Assistant.
5. Add SmartAlarm through **Settings → Devices & services**.

### Event cache

The integration maintains a small local cache of relevant SmartAlarm events. This helps make recent event information available after a Home Assistant restart.

The cache is limited to the **200 most recent relevant events**. It is not intended to replace Home Assistant's recorder or history functionality.

Motion events are deliberately excluded from the persistent event cache because motion is a short-lived state that should be represented by the sensor entity and Home Assistant history.

### Sensor states after restart

After a restart, cached event information can temporarily provide the last known state while SmartAlarm reconnects.

Once the current device status becomes available, the live status takes priority over cached information. This prevents an old event from permanently overriding the actual state of a door, window or other sensor.

### Troubleshooting

If the integration does not appear:

1. Confirm that the files are located in `/config/custom_components/smartalarm/`.
2. Restart Home Assistant.
3. Check **Settings → Devices & services**.
4. Check the Home Assistant logs for SmartAlarm errors.

If a sensor displays an incorrect state after a restart, allow some time for the SmartAlarm connection to synchronize the current device status.

### Development and testing

The integration continues to be developed and tested before changes are published as official releases. For production installations, use an official release whenever possible.

### Disclaimer

This is an independent, community-developed Home Assistant integration. It is not an official SmartAlarm product.

Use it at your own risk. SmartAlarm API behavior and availability may change without notice.

### License

Refer to the repository for the applicable license and project information.
