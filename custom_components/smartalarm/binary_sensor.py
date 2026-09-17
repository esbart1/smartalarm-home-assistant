from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BASE_ID, DOMAIN, STATE_AWAY, STATE_HOME, STATE_DISARM

EXCLUDED = ("afstandsbediening", "bedieningspaneel")
FIRE_KINDS = ("smoke", "co")


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
    if "bewegingsmelder" in n:
        return "motion"
    if "deur" in n:
        return "door"
    if "raam" in n or "serre" in n:
        return "window"
    if "rook" in n or "hitte" in n:
        return "smoke"
    if "koolmonoxide" in n or "koolstofmonoxide" in n or n == "co" or " co " in n:
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


def _event_is_tamper(event: dict) -> bool:
    text = str(event.get("message") or "").casefold()
    state = event.get("state")
    if isinstance(state, dict):
        text += " " + str(state.get("human_readable") or "").casefold()
        text += " " + str(state.get("value") or "").casefold()
    return "sabotage" in text or "tamper" in text


def _event_tamper_cleared(event: dict) -> bool:
    text = str(event.get("message") or "").casefold()
    return any(term in text for term in (
        "sabotage opgeheven",
        "sabotage hersteld",
        "geen sabotage",
        "tamper hersteld",
        "tamper cleared",
    ))


def _latest_tamper_state(events, device_id):
    for event in events or []:
        try:
            if int(event.get("device_id")) != int(device_id):
                continue
        except (TypeError, ValueError):
            continue
        if not _event_is_tamper(event):
            continue
        return not _event_tamper_cleared(event)
    return False


class SmartAlarmFirePanelSensor(CoordinatorEntity, BinarySensorEntity):
    """Aggregate fire alarm state for all smoke/heat and CO sensors."""

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
        devices = self.dc.data or []
        for device in devices:
            try:
                did = int(device.get("id"))
            except (TypeError, ValueError):
                continue
            k = kind(str(device.get("name") or ""))
            if k not in FIRE_KINDS:
                continue
            state = _device_state(self.coordinator.data, did)
            if state in ("trigger", "alarm", "on", "open"):
                return True
        return False

    @property
    def extra_state_attributes(self):
        active = []
        for device in self.dc.data or []:
            try:
                did = int(device.get("id"))
            except (TypeError, ValueError):
                continue
            k = kind(str(device.get("name") or ""))
            if k not in FIRE_KINDS:
                continue
            state = _device_state(self.coordinator.data, did)
            if state in ("trigger", "alarm", "on", "open"):
                active.append({"device_id": did, "name": str(device.get("name") or did), "type": k, "state": state})
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


class SmartAlarmIntrusionSensor(CoordinatorEntity, BinarySensorEntity):
    """Indicates a security intrusion that occurred during the current armed period."""

    _attr_name = "SmartAlarm inbraak melding"
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:alarm-light"

    def __init__(self, fast, entry):
        super().__init__(fast)
        self._attr_unique_id = f"{entry.entry_id}_intrusion"

    @property
    def is_on(self):
        data = self.coordinator.data or {}
        alarm_state = data.get("state")
        if alarm_state not in (STATE_AWAY, STATE_HOME):
            return False

        events = list(data.get("history", []) or data.get("events", []) or [])
        events.sort(key=self._event_sort_key, reverse=True)

        for event in events:
            kind = self._security_event_kind(event)
            if kind == "disarmed":
                return False
            if kind == "armed":
                return False
            if kind == "intrusion":
                return True

        return False

    @staticmethod
    def _event_sort_key(event: dict):
        created = str(event.get("created_at") or "")
        try:
            return (created, int(event.get("id") or 0))
        except (TypeError, ValueError):
            return (created, 0)

    @classmethod
    def _security_event_kind(cls, event: dict) -> str | None:
        message = str(event.get("message") or "").casefold()
        device_id = event.get("device_id")

        if "inbraakbeveiliging is uitgeschakeld" in message or "alarm uitgeschakeld" in message:
            return "disarmed"
        if "inbraakbeveiliging is ingeschakeld" in message or "alarm ingeschakeld" in message:
            return "armed"

        if cls._is_intrusion_event(event):
            return "intrusion"

        if device_id is not None and cls._is_tamper_text(message):
            return None

        return None

    @staticmethod
    def _is_tamper_text(message: str) -> bool:
        return "sabotage" in message or "tamper" in message

    @classmethod
    def _is_intrusion_event(cls, event: dict) -> bool:
        message = str(event.get("message") or "").casefold()
        device_id = event.get("device_id")

        if cls._is_tamper_text(message):
            return False

        sensor_terms = (
            "beweging gedetecteerd",
            "bewegingsmelder",
            "is nu open",
            "deur is open",
            "raam is open",
            "serre is open",
            "alarm geactiveerd",
            "alarm afgegaan",
            "inbraak",
            "intrusion",
            "trigger",
        )
        if device_id is not None and any(term in message for term in sensor_terms):
            return True

        if device_id is None and any(term in message for term in (
            "alarm geactiveerd",
            "alarm afgegaan",
            "inbraakalarm",
            "inbraak gemeld",
            "inbraak",
            "intrusion",
        )):
            return True

        return False

    @property
    def device_info(self):
        return _panel_device_info()

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        events = list(data.get("history", []) or data.get("events", []) or [])
        events.sort(key=self._event_sort_key, reverse=True)
        for event in events:
            if self._security_event_kind(event) == "intrusion":
                return {
                    "laatste_inbraakmelding": event.get("created_at"),
                    "laatste_inbraakbericht": event.get("message"),
                    "laatste_inbraak_device_id": event.get("device_id"),
                }
        return {
            "laatste_inbraakmelding": None,
            "laatste_inbraakbericht": None,
            "laatste_inbraak_device_id": None,
        }


class _BaseSmartAlarmBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, fast, dc, entry, device_id: int, name: str, suffix: str):
        super().__init__(fast)
        self.fast = fast
        self.dc = dc
        self._device_id = device_id
        self._device_name = name.strip() or str(device_id)
        self._attr_unique_id = f"{entry.entry_id}_device_{device_id}_{suffix}"

    def _kind_is_fire_device(self) -> bool:
        n = self._device_name.casefold()
        return (
            "rook" in n
            or "hitte" in n
            or "koolmonoxide" in n
            or "koolstofmonoxide" in n
            or n == "co"
            or " co " in f" {n} "
        )

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
        if self._kind_is_fire_device():
            info["via_device"] = (DOMAIN, f"fire_panel_{BASE_ID}")
        return DeviceInfo(**info)


class SmartAlarmBinarySensor(_BaseSmartAlarmBinary):
    def __init__(self, fast, dc, entry, device_id, kind_name, name):
        super().__init__(fast, dc, entry, device_id, name, kind_name)
        self._kind = kind_name
        self._attr_device_class = {
            "motion": BinarySensorDeviceClass.MOTION,
            "door": BinarySensorDeviceClass.DOOR,
            "window": BinarySensorDeviceClass.WINDOW,
            "smoke": BinarySensorDeviceClass.SMOKE,
            "co": BinarySensorDeviceClass.CO,
        }.get(kind_name)

    @property
    def name(self):
        self._refresh_name()
        return self._device_name

    @property
    def is_on(self):
        state = _device_state(self.fast.data, self._device_id)
        if self._kind == "motion":
            return state in ("trigger", "open", "on", "alarm")
        if self._kind in ("door", "window"):
            return state in ("open", "trigger", "on", "alarm")
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
