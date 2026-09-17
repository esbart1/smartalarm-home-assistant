"""
Smart Alarm for Home Assistant
"""

from __future__ import annotations

from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import SmartAlarmApi

PLATFORMS = ["sensor", "binary_sensor", "alarm_control_panel"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = SmartAlarmApi(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    coordinator = DataUpdateCoordinator(
        hass,
        logger=__import__("logging").getLogger(__name__),
        name="SmartAlarm",
        update_method=api.async_update,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["api"].async_close()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
