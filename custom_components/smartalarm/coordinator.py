from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartAlarmApi
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartAlarmCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fast 5-second coordinator with persistent event history."""

    def __init__(self, hass: HomeAssistant, api: SmartAlarmApi) -> None:
        super().__init__(hass, _LOGGER, name="SmartAlarm", update_method=self._async_update, update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.api = api
        self.history_path = Path(hass.config.path("custom_components", DOMAIN, "alarm_cache", "smartalarm_events.json"))
        self._history: list[dict[str, Any]] = []

    async def async_initialize(self) -> None:
        try:
            self._history = await self.hass.async_add_executor_job(self._read_history)
        except Exception as err:
            _LOGGER.warning("SmartAlarm gebeurtenissencache lezen mislukt: %s", err)
            self._history = []

    def _read_history(self) -> list[dict[str, Any]]:
        if not self.history_path.exists():
            return []
        value = json.loads(self.history_path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []

    def _write_history(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.history_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._history, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.history_path)

    @staticmethod
    def _sort_key(event: dict[str, Any]) -> tuple[str, int]:
        try:
            event_id = int(event.get("id") or 0)
        except (TypeError, ValueError):
            event_id = 0
        return str(event.get("created_at") or ""), event_id

    async def _async_update(self) -> dict[str, Any]:
        try:
            parsed = await self.api.async_update()
        except Exception as err:
            raise UpdateFailed(f"SmartAlarm update failed: {err}") from err

        by_key = {(str(e.get("created_at") or ""), str(e.get("id") or ""), str(e.get("message") or ""), str(e.get("device_id") or "")): e for e in self._history}
        for event in parsed.get("events", []):
            key = (str(event.get("created_at") or ""), str(event.get("id") or ""), str(event.get("message") or ""), str(event.get("device_id") or ""))
            by_key[key] = event
        self._history = sorted(by_key.values(), key=self._sort_key, reverse=True)[:500]
        if parsed.get("events"):
            try:
                await self.hass.async_add_executor_job(self._write_history)
            except Exception as err:
                _LOGGER.warning("SmartAlarm gebeurtenissencache schrijven mislukt: %s", err)
        parsed["history"] = self._history
        return parsed
