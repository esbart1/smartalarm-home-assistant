from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import BASE_ID, DOMAIN, SIGNAL_STALE_AFTER_MINUTES, STATE_NAMES
from .signal_store import SmartAlarmSignalStore


def _base_info() -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"base_{BASE_ID}")},
        name="SmartAlarm alarmpaneel",
        manufacturer="SmartAlarm",
        model="Alarmcentrale",
    )


def _device_name(devices, device_id: int, fallback: str) -> str:
    for device in devices or []:
        try:
            if int(device.get("id")) == device_id:
                return str(device.get("name") or fallback).strip()
        except (TypeError, ValueError):
            pass
    return fallback


def _age_text(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = dt_util.parse_datetime(value)
        if parsed is None:
            return None
        seconds = max(0, int((dt_util.utcnow() - parsed.astimezone(dt_util.UTC)).total_seconds()))
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        if days:
            return f"{days} dag(en) geleden"
        if hours:
            return f"{hours} uur, {minutes} min geleden"
        if minutes:
            return f"{minutes} min, {secs} sec geleden"
        return f"{secs} sec geleden"
    except (TypeError, ValueError, AttributeError):
        return None


def _stale(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed = dt_util.parse_datetime(value)
        if parsed is None:
            return True
        return (dt_util.utcnow() - parsed.astimezone(dt_util.UTC)) > timedelta(minutes=SIGNAL_STALE_AFTER_MINUTES)
    except (TypeError, ValueError, AttributeError):
        return True


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    devices = data["device_coordinator"]
    store: SmartAlarmSignalStore = data["signal_store"]

    registry = er.async_get(hass)
    for device in devices.data or []:
        try:
            did = int(device["id"])
        except (KeyError, TypeError, ValueError):
            continue
        for suffix in ("signal_normal_threshold", "signal_warning_threshold"):
            old_unique_id = f"{entry.entry_id}_device_{did}_{suffix}"
            old_entity_id = registry.async_get_entity_id("sensor", DOMAIN, old_unique_id)
            if old_entity_id:
                registry.async_remove(old_entity_id)

    entities = [
        SmartAlarmStatusSensor(coordinator, entry),
        SmartAlarmLastEventSensor(coordinator, entry),
    ]
    known: set[int] = set()
    for device in devices.data or []:
        try:
            did = int(device["id"])
        except (KeyError, TypeError, ValueError):
            continue
        known.add(did)
        entities.extend(_device_entities(devices, store, entry, device))
    async_add_entities(entities)

    def add_new_devices():
        new = []
        for device in devices.data or []:
            try:
                did = int(device["id"])
            except (KeyError, TypeError, ValueError):
                continue
            if did not in known:
                known.add(did)
                new.extend(_device_entities(devices, store, entry, device))
        if new:
            async_add_entities(new)

    devices.async_add_listener(add_new_devices)


def _device_entities(devices, store, entry, device):
    return [
        SmartAlarmDeviceSignalSensor(devices, store, entry, device),
        SmartAlarmDeviceSignalStatusSensor(devices, store, entry, device),
        SmartAlarmDeviceCalibrationSensor(devices, store, entry, device),
        SmartAlarmDeviceLastSignalSensor(devices, store, entry, device),
        SmartAlarmDeviceSignalDiagnosisSensor(devices, store, entry, device),
    ]


class SmartAlarmStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "SmartAlarm status"
    _attr_icon = "mdi:shield-home"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self):
        state = (self.coordinator.data or {}).get("state")
        return STATE_NAMES.get(state, state or "Onbekend")

    @property
    def device_info(self):
        return _base_info()


class SmartAlarmLastEventSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "SmartAlarm laatste melding"
    _attr_icon = "mdi:bell"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_event"

    @property
    def native_value(self):
        history = (self.coordinator.data or {}).get("history", [])
        return str(history[0].get("message") or "Onbekende melding") if history else "Geen meldingen"

    @property
    def extra_state_attributes(self):
        history = (self.coordinator.data or {}).get("history", [])
        return {"event_count": len(history), "events": history}

    @property
    def device_info(self):
        return _base_info()


class _BaseDeviceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator)
        self.store = store
        self.device_id = int(device["id"])
        self.device_name = str(device.get("name") or self.device_id).strip()

    def _refresh_name(self):
        self.device_name = _device_name(self.coordinator.data, self.device_id, self.device_name)

    @property
    def device_info(self):
        self._refresh_name()
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            name=self.device_name,
            manufacturer="SmartAlarm",
            model="SmartAlarm apparaat",
        )

    def _signal(self):
        for device in self.coordinator.data or []:
            try:
                if int(device.get("id")) == self.device_id:
                    return device.get("signal_strength")
            except (TypeError, ValueError):
                pass
        return None


class SmartAlarmDeviceSignalSensor(_BaseDeviceSensor):
    _attr_icon = "mdi:signal"
    _attr_native_unit_of_measurement = "dB"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaalsterkte"

    @property
    def native_value(self):
        return self._signal()

    @property
    def available(self):
        return self._signal() is not None

    @property
    def extra_state_attributes(self):
        item = self.store.get(self.device_id)
        return {
            "referentie": self.store.reference(self.device_id),
            "gekalibreerd_op": item.get("calibrated_at"),
            "kalibratie_leeftijd": _age_text(item.get("calibrated_at")),
            "laatste_signaal": item.get("last_signal_at"),
            "laatste_signaal_waarde": item.get("last_signal_value"),
            "signaal_verouderd": _stale(item.get("last_signal_at")),
            "normale_grens": self.store.normal_threshold(self.device_id),
            "waarschuwingsgrens": self.store.warning_threshold(self.device_id),
        }


class SmartAlarmDeviceSignalStatusSensor(_BaseDeviceSensor):
    _attr_icon = "mdi:signal-variant"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_status"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaalstatus"

    @property
    def native_value(self):
        item = self.store.get(self.device_id)
        current = self._signal()
        if item.get("calibration_error"):
            return "Kalibratie mislukt"
        if self.store.is_calibrating(self.device_id):
            done, total = self.store.calibration_progress(self.device_id)
            return f"Kalibreren ({done}/{total})"
        if _stale(item.get("last_signal_at")):
            return "Geen recent signaal"
        try:
            current = float(current)
        except (TypeError, ValueError):
            current = None
        return self.store.status(self.device_id, current)

    @property
    def available(self):
        return any(str(d.get("id")) == str(self.device_id) for d in (self.coordinator.data or []))

    @property
    def extra_state_attributes(self):
        item = self.store.get(self.device_id)
        done, total = self.store.calibration_progress(self.device_id)
        return {
            "referentie": self.store.reference(self.device_id),
            "grens_normaal_vanaf": self.store.normal_threshold(self.device_id),
            "grens_lager_dan_normaal_vanaf": self.store.warning_threshold(self.device_id),
            "kalibratie_metingen": f"{done}/{total}" if self.store.is_calibrating(self.device_id) else None,
            "kalibratie_gestart_op": item.get("calibration_started_at"),
            "laatste_signaal": item.get("last_signal_at"),
            "laatste_signaal_leeftijd": _age_text(item.get("last_signal_at")),
        }


class SmartAlarmDeviceCalibrationSensor(_BaseDeviceSensor):
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_calibration"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaal gekalibreerd"

    @property
    def native_value(self):
        value = self.store.calibrated_at(self.device_id)
        if not value:
            return "Nooit"
        try:
            parsed = dt_util.parse_datetime(value)
            return dt_util.as_local(parsed).strftime("%d-%m-%Y %H:%M:%S") if parsed else value
        except (TypeError, ValueError, AttributeError):
            return value

    @property
    def extra_state_attributes(self):
        return {
            "referentie": self.store.reference(self.device_id),
            "normale_grens": self.store.normal_threshold(self.device_id),
            "waarschuwingsgrens": self.store.warning_threshold(self.device_id),
        }


class SmartAlarmDeviceLastSignalSensor(_BaseDeviceSensor):
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_last_signal"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} laatste signaal"

    @property
    def native_value(self):
        value = self.store.last_signal_at(self.device_id)
        if not value:
            return "Nooit"
        try:
            parsed = dt_util.parse_datetime(value)
            return dt_util.as_local(parsed).strftime("%d-%m-%Y %H:%M:%S") if parsed else value
        except (TypeError, ValueError, AttributeError):
            return str(value)

    @property
    def extra_state_attributes(self):
        value = self.store.last_signal_at(self.device_id)
        return {
            "laatste_signaal_waarde": self.store.last_signal_value(self.device_id),
            "signaal_verouderd": _stale(value),
            "signaal_verouderd_na_minuten": SIGNAL_STALE_AFTER_MINUTES,
        }


class SmartAlarmDeviceSignalDiagnosisSensor(_BaseDeviceSensor):
    _attr_icon = "mdi:signal-variant"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_diagnosis"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaal diagnose"

    def _trend(self, item):
        history = [
            h for h in (item.get("signal_history") or [])
            if isinstance(h, dict) and isinstance(h.get("avg"), (int, float))
        ]
        if len(history) < 2:
            return None, None
        recent = float(history[-1]["avg"])
        previous = [float(h["avg"]) for h in history[-4:-1]]
        if not previous:
            return None, recent
        baseline = sum(previous) / len(previous)
        delta = recent - baseline
        return ("Dalend" if delta <= -5 else "Stijgend" if delta >= 5 else "Stabiel"), recent

    @property
    def native_value(self):
        item = self.store.get(self.device_id)
        if item.get("calibration_error"):
            return "Kalibratie mislukt"
        if _stale(item.get("last_signal_at")):
            return "Geen recent signaal"
        reference = self.store.reference(self.device_id)
        if reference is None:
            return "Nog niet gekalibreerd"
        try:
            current = float(self._signal())
        except (TypeError, ValueError):
            return "Geen recent signaal"
        trend, _ = self._trend(item)
        warning = self.store.warning_threshold(self.device_id)
        normal = self.store.normal_threshold(self.device_id)
        if warning is not None and current < warning:
            return "Sterk verzwakt - dalende trend" if trend == "Dalend" else "Sterk verzwakt"
        if normal is not None and current < normal:
            return "Lager dan normaal - dalende trend" if trend == "Dalend" else "Lager dan normaal"
        if trend == "Dalend":
            return "Dalende signaaltrend - controleren"
        return "Normaal"

    @property
    def extra_state_attributes(self):
        item = self.store.get(self.device_id)
        trend, recent = self._trend(item)
        return {
            "referentie": self.store.reference(self.device_id),
            "actueel_signaal": self._signal(),
            "normale_grens": self.store.normal_threshold(self.device_id),
            "waarschuwingsgrens": self.store.warning_threshold(self.device_id),
            "signaaltrend": trend,
            "gemiddelde_laatste_uur": recent,
            "laatste_signaal": item.get("last_signal_at"),
            "gekalibreerd_op": item.get("calibrated_at"),
        }
