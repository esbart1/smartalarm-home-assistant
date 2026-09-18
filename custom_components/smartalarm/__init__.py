from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .api import SmartAlarmApi
from .const import DOMAIN
from .coordinator import SmartAlarmCoordinator
from .device_coordinator import SmartAlarmDeviceCoordinator
from .signal_store import SmartAlarmSignalStore

PLATFORMS = ["sensor", "binary_sensor", "button", "number", "alarm_control_panel"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = SmartAlarmApi(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    signal_store = SmartAlarmSignalStore(hass)
    await signal_store.async_load()

    coordinator = SmartAlarmCoordinator(hass, api)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    device_coordinator = SmartAlarmDeviceCoordinator(hass, api, signal_store)
    await device_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "device_coordinator": device_coordinator,
        "signal_store": signal_store,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["api"].async_close()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
