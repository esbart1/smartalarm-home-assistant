from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartAlarmApi
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartAlarmCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fast 5-second coordinator with a compact persistent event history."""

    def __init__(self, hass: HomeAssistant, api: SmartAlarmApi) -> None:
        super().__init__(hass, _LOGGER, name="SmartAlarm", update_method=self._async_update, update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.api = api
        self._store = Store(hass, 1, f"{DOMAIN}_{api.email.casefold()}_events")
        self._history: list[dict[str, Any]] = []
        self._history_max_events = 200
        self._history_load_ok = True

    async def async_initialize(self) -> None:
        try:
            stored = await self._store.async_load()
            loaded = stored if isinstance(stored, list) else []
        except Exception as err:
            _LOGGER.warning("SmartAlarm gebeurtenissencache lezen mislukt: %s", err)
            self._history_load_ok = False
            return

        filtered = [event for event in loaded if self._is_significant_event(event)]
        self._history = sorted(filtered, key=self._sort_key, reverse=True)[: self._history_max_events]
        if len(filtered) != len(loaded) or len(self._history) != len(filtered):
            try:
                await self._store.async_save(self._history)
            except Exception as err:
                _LOGGER.warning("SmartAlarm gebeurtenissencache opschonen mislukt: %s", err)

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
        """Persist all useful events except frequent, short-lived motion events."""
        text = cls._event_text(event)
        if "beweging gedetecteerd" in text or "bewegingsmelder" in text:
            return False
        return True


    async def _async_update(self) -> dict[str, Any]:
        try:
            parsed = await self.api.async_update()
        except ConfigEntryAuthFailed:
            raise
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
                await self._store.async_save(self._history)
            except Exception as err:
                _LOGGER.warning("SmartAlarm gebeurtenissencache schrijven mislukt: %s", err)
        # Keep current API events in memory for live motion/intrusion handling,
        # but only persist the filtered history to disk.
        live_by_key = {
            (
                str(e.get("created_at") or ""),
                str(e.get("id") or ""),
                str(e.get("message") or ""),
                str(e.get("device_id") or ""),
            ): e
            for e in self._history
        }
        for event in parsed.get("events", []):
            key = (
                str(event.get("created_at") or ""),
                str(event.get("id") or ""),
                str(event.get("message") or ""),
                str(event.get("device_id") or ""),
            )
            live_by_key[key] = event
        parsed["history"] = sorted(
            live_by_key.values(), key=self._sort_key, reverse=True
        )[: self._history_max_events]
        return parsed
