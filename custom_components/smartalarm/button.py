from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["device_coordinator"]
    store = data["signal_store"]
    known = set()
    entities = []
    for device in coordinator.data or []:
        try:
            did = int(device["id"])
        except (KeyError, TypeError, ValueError):
            continue
        known.add(did)
        entities.append(SmartAlarmSignalCalibrateButton(coordinator, store, entry, device))
    async_add_entities(entities)

    def add_new():
        new = []
        for device in coordinator.data or []:
            try:
                did = int(device["id"])
            except (KeyError, TypeError, ValueError):
                continue
            if did not in known:
                known.add(did)
                new.append(SmartAlarmSignalCalibrateButton(coordinator, store, entry, device))
        if new:
            async_add_entities(new)
    coordinator.async_add_listener(add_new)


class SmartAlarmSignalCalibrateButton(CoordinatorEntity, ButtonEntity):
    _attr_icon = "mdi:signal-sync"

    def __init__(self, coordinator, store, entry, device):
        super().__init__(coordinator)
        self.store = store
        self.device_id = int(device["id"])
        self.device_name = str(device.get("name") or self.device_id).strip()
        self._attr_unique_id = f"{entry.entry_id}_device_{self.device_id}_signal_calibrate"

    def _refresh(self):
        for device in self.coordinator.data or []:
            try:
                if int(device.get("id")) == self.device_id:
                    self.device_name = str(device.get("name") or self.device_name).strip()
                    break
            except (TypeError, ValueError):
                pass

    @property
    def name(self):
        self._refresh()
        return f"{self.device_name} signaal kalibreren"

    @property
    def available(self):
        return any(str(d.get("id")) == str(self.device_id) for d in (self.coordinator.data or []))

    async def async_press(self):
        await self.store.async_start_calibration(self.device_id, self.device_name)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        self._refresh()
        return DeviceInfo(identifiers={(DOMAIN, str(self.device_id))}, name=self.device_name, manufacturer="SmartAlarm", model="SmartAlarm apparaat")
