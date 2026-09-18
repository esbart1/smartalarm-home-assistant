from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .signal_store import SmartAlarmSignalStore


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["device_coordinator"]
    store: SmartAlarmSignalStore = data["signal_store"]

    known: set[int] = set()
    entities = []

    for device in coordinator.data or []:
        try:
            did = int(device["id"])
        except (KeyError, TypeError, ValueError):
            continue
        known.add(did)
        entities.extend(_device_entities(coordinator, store, entry, device))

    async_add_entities(entities)

    def add_new_devices():
        new = []
        for device in coordinator.data or []:
            try:
                did = int(device["id"])
            except (KeyError, TypeError, ValueError):
                continue
            if did not in known:
                known.add(did)
                new.extend(_device_entities(coordinator, store, entry, device))
        if new:
            async_add_entities(new)

    coordinator.async_add_listener(add_new_devices)


def _device_entities(coordinator, store, entry, device):
    return [
        SmartAlarmDeviceNormalThresholdNumber(coordinator, store, entry, device),
        SmartAlarmDeviceWarningThresholdNumber(coordinator, store, entry, device),
    ]


class _BaseThresholdNumber(CoordinatorEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 50.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator)
        self.store = store
        self.device_id = int(device["id"])
        self.device_name = str(device.get("name") or self.device_id).strip()

    def _refresh_name(self):
        for device in self.coordinator.data or []:
            try:
                if int(device.get("id")) == self.device_id:
                    self.device_name = str(device.get("name") or self.device_name).strip()
                    break
            except (TypeError, ValueError):
                pass

    @property
    def device_info(self) -> DeviceInfo:
        self._refresh_name()
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            name=self.device_name,
            manufacturer="SmartAlarm",
            model="SmartAlarm apparaat",
        )

    @property
    def available(self) -> bool:
        return self.store.reference(self.device_id) is not None


class SmartAlarmDeviceNormalThresholdNumber(_BaseThresholdNumber):
    _attr_icon = "mdi:signal-strength-4"
    _attr_native_max_value = 100.0

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_normal_threshold"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaalgrens normaal"

    @property
    def native_value(self):
        return round(self.store.normal_ratio(self.device_id) * 100.0, 1)

    @property
    def extra_state_attributes(self):
        return {
            "referentie": self.store.reference(self.device_id),
            "berekende_grens_db": self.store.normal_threshold(self.device_id),
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.store.async_set_normal_ratio(self.device_id, value)
        self.async_write_ha_state()


class SmartAlarmDeviceWarningThresholdNumber(_BaseThresholdNumber):
    _attr_icon = "mdi:signal-off"
    _attr_native_max_value = 99.0

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator, store, entry, device)
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_warning_threshold"

    @property
    def name(self):
        self._refresh_name()
        return f"{self.device_name} signaalgrens waarschuwing"

    @property
    def native_value(self):
        return round(self.store.warning_ratio(self.device_id) * 100.0, 1)

    @property
    def extra_state_attributes(self):
        return {
            "referentie": self.store.reference(self.device_id),
            "berekende_grens_db": self.store.warning_threshold(self.device_id),
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.store.async_set_warning_ratio(self.device_id, value)
        self.async_write_ha_state()
