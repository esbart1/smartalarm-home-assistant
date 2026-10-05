# Changelog

## 0.4.9 - testversie

- Verbeterde verwerking van deur- en raambinary sensors na een Home Assistant-herstart.
- Actuele SmartAlarm-apparatenstatus is de primaire bron voor contactstatus.
- Opgeslagen relevante gebeurtenis is een tijdelijke tweede bron wanneer actuele apparaatdata nog niet beschikbaar is.
- Bewegingsmelders vallen na 500 ms terug naar `Niet gedetecteerd`.
- Bewegingsmeldingen worden niet meer persistent opgeslagen.
- Cache beperkt tot maximaal 200 relevante gebeurtenissen.
- Compactere en duidelijkere meldingen.
- Korte alarmstatussen: `Aan`, `Thuis`, `Uit`.
