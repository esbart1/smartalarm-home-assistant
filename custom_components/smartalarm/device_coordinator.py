from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartAlarmApi
from .const import DEVICE_SCAN_INTERVAL
from .signal_store import SmartAlarmSignalStore

_LOGGER = logging.getLogger(__name__)


class SmartAlarmDeviceCoordinator(DataUpdateCoordinator[list[dict]]):
    """Separate 30-second coordinator for the full devices page."""

    def __init__(self, hass: HomeAssistant, api: SmartAlarmApi, signal_store: SmartAlarmSignalStore) -> None:
        super().__init__(hass, _LOGGER, name="SmartAlarm apparaten", update_method=self._async_update, update_interval=timedelta(seconds=DEVICE_SCAN_INTERVAL))
        self.api = api
        self.signal_store = signal_store

    async def _async_update(self) -> list[dict]:
        try:
            devices = await self.api.async_get_devices()
            if not devices and self.data:
                _LOGGER.warning("SmartAlarm: lege apparatenlijst; oude lijst behouden")
                return self.data
            await self.signal_store.async_process_devices(devices)
            return devices
        except Exception as err:
            if self.data:
                _LOGGER.warning("SmartAlarm apparaten ophalen mislukt: %s; oude lijst behouden", err)
                return self.data
            raise UpdateFailed(f"SmartAlarm devices update failed: {err}") from err
