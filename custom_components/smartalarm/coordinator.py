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
    """Fast 5-second coordinator with a compact persistent event history."""

    def __init__(self, hass: HomeAssistant, api: SmartAlarmApi) -> None:
        super().__init__(hass, _LOGGER, name="SmartAlarm", update_method=self._async_update, update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.api = api
        self.history_path = Path(hass.config.path("custom_components", DOMAIN, "alarm_cache", "smartalarm_events.json"))
        self._history: list[dict[str, Any]] = []
        self._history_max_events = 200
        self._history_load_ok = True

    async def async_initialize(self) -> None:
        try:
            loaded = await self.hass.async_add_executor_job(self._read_history)
        except Exception as err:
            _LOGGER.warning("SmartAlarm gebeurtenissencache lezen mislukt: %s", err)
            self._history_load_ok = False
            return

        filtered = [event for event in loaded if self._is_significant_event(event)]
        self._history = sorted(filtered, key=self._sort_key, reverse=True)[: self._history_max_events]
        if len(filtered) != len(loaded) or len(self._history) != len(filtered):
            try:
                await self.hass.async_add_executor_job(self._write_history)
            except Exception as err:
                _LOGGER.warning("SmartAlarm gebeurtenissencache opschonen mislukt: %s", err)

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

    @staticmethod
    def _event_text(event: dict[str, Any]) -> str:
        text = str(event.get("message") or "")
        state = event.get("state")
        if isinstance(state, dict):
            text += " " + str(state.get("human_readable") or "")
            text += " " + str(state.get("value") or "")
        else:
            text += " " + str(state or "")
        return text.casefold()

    @classmethod
    def _is_significant_event(cls, event: dict[str, Any]) -> bool:
        """Keep security-relevant events; ordinary sensor chatter belongs in HA Recorder."""
        text = cls._event_text(event)

        if event.get("device_id") is None:
            return True

        if "sabotage" in text or "tamper" in text:
            return True

        if any(term in text for term in (
            "brand", "rook", "hitte", "smoke", "fire",
            "koolmonoxide", "koolstofmonoxide", "co-melding", "co melding",
        )):
            return True

        if any(term in text for term in (
            "inbraak", "intrusion", "alarm geactiveerd",
            "alarm afgegaan", "alarm triggered", "trigger",
        )):
            return True

        return False


    async def _async_update(self) -> dict[str, Any]:
        try:
            parsed = await self.api.async_update()
        except Exception as err:
            raise UpdateFailed(f"SmartAlarm update failed: {err}") from err

        by_key = {
            (
                str(e.get("created_at") or ""),
                str(e.get("id") or ""),
                str(e.get("message") or ""),
                str(e.get("device_id") or ""),
            ): e
            for e in self._history
            if self._is_significant_event(e)
        }
        for event in parsed.get("events", []):
            if not self._is_significant_event(event):
                continue
            key = (
                str(event.get("created_at") or ""),
                str(event.get("id") or ""),
                str(event.get("message") or ""),
                str(event.get("device_id") or ""),
            )
            by_key[key] = event
        self._history = sorted(
            by_key.values(), key=self._sort_key, reverse=True
        )[: self._history_max_events]
        if parsed.get("events") and self._history_load_ok:
            try:
                await self.hass.async_add_executor_job(self._write_history)
            except Exception as err:
                _LOGGER.warning("SmartAlarm gebeurtenissencache schrijven mislukt: %s", err)
        parsed["history"] = self._history
        return parsed
