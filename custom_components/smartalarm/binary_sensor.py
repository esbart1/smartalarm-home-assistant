from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BASE_ID, DOMAIN, STATE_AWAY, STATE_HOME

EXCLUDED = ("afstandsbediening",)
FIRE_KINDS = ("smoke", "co")
CLEAR_TERMS = (
    "sabotage opgeheven",
    "sabotage hersteld",
    "geen sabotage",
    "tamper hersteld",
    "tamper cleared",
    "alarm opgeheven",
    "alarm hersteld",
    "alarm uit",
    "geen brand",
    "geen rook",
    "geen co",
    "geen koolmonoxide",
    "geen koolstofmonoxide",
)
FIRE_TERMS = (
    "brand",
    "rook",
    "hitte",
    "smoke",
    "fire",
    "koolmonoxide",
    "koolstofmonoxide",
    "co-melding",
    "co melding",
)


def _panel_device_info() -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"base_{BASE_ID}")},
        name="SmartAlarm alarmpaneel",
        manufacturer="SmartAlarm",
        model="Alarmcentrale",
    )


def _fire_panel_device_info() -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"fire_panel_{BASE_ID}")},
        name="SmartAlarm brandalarmpaneel",
        manufacturer="SmartAlarm",
        model="Brandalarm",
    )


def kind(name: str):
    n = name.casefold()
    if any(x in n for x in EXCLUDED):
        return None
    if "bedieningspaneel" in n:
        return "panel"
    if "bewegingsmelder" in n:
        return "motion"
    if "deur" in n:
        return "door"
    if "raam" in n or "serre" in n:
        return "window"
    if "rook" in n or "hitte" in n:
        return "smoke"
    if "koolmonoxide" in n or "koolstofmonoxide" in n or n == "co" or " co " in f" {n} ":
        return "co"
    return None


def _device_by_id(devices, device_id):
    for device in devices or []:
        try:
            if int(device.get("id")) == int(device_id):
                return device
        except (TypeError, ValueError):
            continue
    return None


def _device_state(fast_data, device_id):
    device = _device_by_id((fast_data or {}).get("devices", []), device_id)
    if device:
        return str(device.get("state") or "").casefold()
    return ""


def _event_text(event: dict) -> str:
    text = str(event.get("message") or "")
    state = event.get("state")
    if isinstance(state, dict):
        text += " " + str(state.get("human_readable") or "")
        text += " " + str(state.get("value") or "")
    else:
        text += " " + str(state or "")
    return text.casefold()


def _event_matches_device(event: dict, device_id: int) -> bool:
    try:
        return int(event.get("device_id")) == int(device_id)
    except (TypeError, ValueError):
        return False


def _is_fire_alarm_event(event: dict) -> bool:
    text = _event_text(event)
    if any(term in text for term in CLEAR_TERMS):
        return False
    if any(term in text for term in FIRE_TERMS):
        return any(term in text for term in ("alarm", "melding", "gedetecteerd", "geactiveerd", "trigger", "rook", "brand", "hitte", "co"))
    return False


def _is_fire_clear_event(event: dict) -> bool:
    return any(term in _event_text(event) for term in CLEAR_TERMS)


def _latest_fire_state(events, device_id: int) -> bool:
    ordered = sorted(events or [], key=_event_sort_key, reverse=True)
    for event in ordered:
        if not _event_matches_device(event, device_id):
            continue
        if _is_fire_clear_event(event):
            return False
        if _is_fire_alarm_event(event):
            return True
    return False


def _event_sort_key(event: dict):
    created = str(event.get("created_at") or "")
    try:
        return (created, int(event.get("id") or 0))
    except (TypeError, ValueError):
        return (created, 0)


def _event_is_tamper(event: dict) -> bool:
    text = _event_text(event)
    return "sabotage" in text or "tamper" in text


def _event_tamper_cleared(event: dict) -> bool:
    text = _event_text(event)
    return any(term in text for term in CLEAR_TERMS[:5])


def _latest_tamper_state(events, device_id):
    for event in sorted(events or [], key=_event_sort_key, reverse=True):
        if not _event_matches_device(event, device_id):
            continue
        if not _event_is_tamper(event):
            continue
        return not _event_tamper_cleared(event)
    return False


class SmartAlarmFirePanelSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_name = "SmartAlarm brandalarm"
    _attr_device_class = BinarySensorDeviceClass.SMOKE
    _attr_icon = "mdi:fire-alert"

    def __init__(self, fast, dc, entry):
        super().__init__(fast)
        self.dc = dc
        self._attr_unique_id = f"{entry.entry_id}_fire_panel"

    @property
    def device_info(self):
        return _fire_panel_device_info()

    @property
    def is_on(self):
        history = (self.coordinator.data or {}).get("history", [])
        for device in self.dc.data or []:
            try:
                did = int(device.get("id"))
            except (TypeError, ValueError):
                continue
            if kind(str(device.get("name") or "")) in FIRE_KINDS and _latest_fire_state(history, did):
                return True
        return False

    @property
    def extra_state_attributes(self):
        active = []
        history = (self.coordinator.data or {}).get("history", [])
        for device in self.dc.data or []:
            try:
                did = int(device.get("id"))
            except (TypeError, ValueError):
                continue
            fire_kind = kind(str(device.get("name") or ""))
            if fire_kind in FIRE_KINDS and _latest_fire_state(history, did):
                active.append({"device_id": did, "name": str(device.get("name") or did), "type": fire_kind})
        return {"actieve_brandmelders": active, "aantal_actief": len(active)}


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    fast = data["coordinator"]
    dc = data["device_coordinator"]

    existing: set[tuple[int, str]] = set()
    entities = [SmartAlarmIntrusionSensor(fast, entry), SmartAlarmFirePanelSensor(fast, dc, entry)]
    for device in dc.data or []:
        try:
            did = int(device["id"])
        except (KeyError, TypeError, ValueError):
            continue
        k = kind(str(device.get("name") or ""))
        if not k:
            continue
        existing.add((did, k))
        entities.append(SmartAlarmBinarySensor(fast, dc, entry, did, k, str(device.get("name") or did)))
        existing.add((did, "tamper"))
        entities.append(SmartAlarmTamperSensor(fast, dc, entry, did, str(device.get("name") or did)))

    async_add_entities(entities)

    def add_new_devices():
        new = []
        for device in dc.data or []:
            try:
                did = int(device["id"])
            except (KeyError, TypeError, ValueError):
                continue
            k = kind(str(device.get("name") or ""))
            if not k:
                continue
            key = (did, k)
            if key not in existing:
                existing.add(key)
                new.append(SmartAlarmBinarySensor(fast, dc, entry, did, k, str(device.get("name") or did)))
            tamper_key = (did, "tamper")
            if tamper_key not in existing:
                existing.add(tamper_key)
                new.append(SmartAlarmTamperSensor(fast, dc, entry, did, str(device.get("name") or did)))
        if new:
            async_add_entities(new)

    dc.async_add_listener(add_new_devices)


class SmartAlarmIntrusionSensor(CoordinatorEntity, RestoreEntity, BinarySensorEntity):
    _attr_name = "SmartAlarm inbraak melding"
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:alarm-light"

    def __init__(self, fast, entry):
        super().__init__(fast)
        self._attr_unique_id = f"{entry.entry_id}_intrusion"
        self._restored_is_on: bool | None = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state in ("on", "off"):
            self._restored_is_on = state.state == "on"

    @property
    def is_on(self):
        data = self.coordinator.data
        if not data:
            return self._restored_is_on if self._restored_is_on is not None else False
        if data.get("state") not in (STATE_AWAY, STATE_HOME):
            return False
        history = data.get("history")
        if history is None:
            return self._restored_is_on if self._restored_is_on is not None else False
        events = sorted(list(history or []), key=_event_sort_key, reverse=True)
        for event in events:
            kind_name = self._security_event_kind(event)
            if kind_name in ("disarmed", "armed"):
                return False
            if kind_name == "intrusion":
                return True
        return False

    @classmethod
    def _security_event_kind(cls, event: dict) -> str | None:
        message = str(event.get("message") or "").casefold()
        if "inbraakbeveiliging is uitgeschakeld" in message or "alarm uitgeschakeld" in message:
            return "disarmed"
        if "inbraakbeveiliging is ingeschakeld" in message or "alarm ingeschakeld" in message:
            return "armed"
        if cls._is_intrusion_event(event):
            return "intrusion"
        return None

    @classmethod
    def _is_intrusion_event(cls, event: dict) -> bool:
        message = str(event.get("message") or "").casefold()
        if "sabotage" in message or "tamper" in message:
            return False
        sensor_terms = ("beweging gedetecteerd", "bewegingsmelder", "is nu open", "deur is open", "raam is open", "alarm geactiveerd", "alarm afgegaan", "inbraak", "intrusion", "trigger")
        return event.get("device_id") is not None and any(term in message for term in sensor_terms)

    @property
    def device_info(self):
        return _panel_device_info()

    @property
    def extra_state_attributes(self):
        events = sorted(list((self.coordinator.data or {}).get("history", []) or (self.coordinator.data or {}).get("events", []) or []), key=_event_sort_key, reverse=True)
        for event in events:
            if self._security_event_kind(event) == "intrusion":
                return {"laatste_inbraakmelding": event.get("created_at"), "laatste_inbraakbericht": event.get("message"), "laatste_inbraak_device_id": event.get("device_id")}
        return {"laatste_inbraakmelding": None, "laatste_inbraakbericht": None, "laatste_inbraak_device_id": None}


class _BaseSmartAlarmBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, fast, dc, entry, device_id: int, name: str, suffix: str):
        super().__init__(fast)
        self.fast = fast
        self.dc = dc
        self._device_id = device_id
        self._device_name = name.strip() or str(device_id)
        self._attr_unique_id = f"{entry.entry_id}_device_{device_id}_{suffix}"

    def _refresh_name(self):
        device = _device_by_id(self.dc.data, self._device_id)
        if device:
            self._device_name = str(device.get("name") or self._device_name).strip()

    @property
    def device_info(self):
        self._refresh_name()
        info = {
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": self._device_name,
            "manufacturer": "SmartAlarm",
            "model": "SmartAlarm apparaat",
        }
        if kind(self._device_name) in FIRE_KINDS:
            info["via_device"] = (DOMAIN, f"fire_panel_{BASE_ID}")
        return DeviceInfo(**info)


class SmartAlarmBinarySensor(_BaseSmartAlarmBinary, RestoreEntity):
    def __init__(self, fast, dc, entry, device_id, kind_name, name):
        super().__init__(fast, dc, entry, device_id, name, kind_name)
        self._kind = kind_name
        self._restored_is_on: bool | None = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if self._kind not in ("door", "window"):
            return
        state = await self.async_get_last_state()
        if state and state.state in ("on", "off", "open", "closed"):
            self._restored_is_on = state.state in ("on", "open")
        self._attr_device_class = {
            "motion": BinarySensorDeviceClass.MOTION,
            "door": BinarySensorDeviceClass.DOOR,
            "window": BinarySensorDeviceClass.WINDOW,
            "smoke": BinarySensorDeviceClass.SMOKE,
            "co": BinarySensorDeviceClass.CO,
            "panel": BinarySensorDeviceClass.CONNECTIVITY,
        }.get(kind_name)

    @property
    def name(self):
        self._refresh_name()
        return self._device_name if self._kind == "panel" else self._device_name

    @property
    def is_on(self):
        if self._kind in FIRE_KINDS:
            return _latest_fire_state((self.fast.data or {}).get("history", []), self._device_id)
        state = _device_state(self.fast.data, self._device_id)
        if self._kind == "panel":
            if state in ("offline", "unavailable", "disconnected"):
                return False
            return True
        if self._kind == "motion":
            return state in ("trigger", "open", "on", "alarm")
        if self._kind in ("door", "window"):
            if state in ("open", "trigger", "on", "alarm"):
                return True
            if state in ("closed", "normal", "off", "clear"):
                return False
            return self._restored_is_on if self._restored_is_on is not None else False
        return state in ("trigger", "alarm", "on", "open")


class SmartAlarmTamperSensor(_BaseSmartAlarmBinary):
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:shield-alert"

    def __init__(self, fast, dc, entry, device_id, name):
        super().__init__(fast, dc, entry, device_id, name, "tamper")

    @property
    def name(self):
        self._refresh_name()
        return f"{self._device_name} sabotage"

    @property
    def is_on(self):
        events = (self.fast.data or {}).get("history", [])
        return _latest_tamper_state(events, self._device_id)
