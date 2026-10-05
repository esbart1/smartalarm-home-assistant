# SmartAlarm voor Home Assistant

Een custom Home Assistant-integratie voor SmartAlarm. De integratie haalt de SmartAlarm-apparaten en gebeurtenissen op en maakt deze beschikbaar in Home Assistant.

> **Status: testversie 0.4.9**
> Deze versie is eerst uitgebreid getest op een aparte Home Assistant-testinstallatie. Maak voor gebruik altijd een backup.

## Belangrijkste wijzigingen in 0.4.9

- Deur- en raamsensoren worden bijgewerkt vanuit de actuele SmartAlarm-apparatenstatus.
- Bij het opstarten kan de laatste opgeslagen relevante gebeurtenis tijdelijk als tweede bron worden gebruikt wanneer de actuele apparatenstatus nog niet beschikbaar is.
- Bewegingsmelders worden na een detectie kort actief en vallen daarna terug naar `Niet gedetecteerd`.
- Bewegingsmeldingen worden niet opgeslagen in de persistente gebeurteniscache.
- De gebeurteniscache is beperkt tot 200 relevante gebeurtenissen en is bedoeld voor herstel van meldingen na een Home Assistant-herstart, niet als volledige historie.
- De teksten in het SmartAlarm-paneel zijn compacter en duidelijker gemaakt.
- Alarmstatussen gebruiken korte teksten zoals `Aan`, `Thuis` en `Uit`.

## Installatie

### Handmatig

Kopieer de map `custom_components/smartalarm` naar de `config/custom_components/` map van Home Assistant en herstart Home Assistant.

### HACS

Deze repository is voorbereid voor gebruik als custom repository in HACS. Voeg de GitHub-repository toe als **Integration** en installeer daarna SmartAlarm.

## Gebeurteniscache

De integratie gebruikt `config/custom_components/smartalarm/alarm_cache/smartalarm_events.json` voor een beperkte cache van recente relevante gebeurtenissen. Bewegingsmeldingen worden bewust niet in deze cache opgeslagen. De cache is bedoeld om het SmartAlarm-paneel na een reboot te kunnen herstellen.

## Problemen melden

Gebruik de Issues-pagina van deze repository en vermeld Home Assistant-versie, integratieversie en relevante logregels. Plaats geen wachtwoorden of andere privégegevens.
