from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN, EVENT_CACHE_MAX

_LOGGER = logging.getLogger(__name__)


class SmartAlarmEventStore:
    """Persistent history of every SmartAlarm event seen by this integration."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        cache_dir = Path(hass.config.path("custom_components", DOMAIN, "alarm_cache"))
        self.path = cache_dir / "smartalarm_events.json"
        # Old versions used the entry_id as the filename. Keep this for migration.
        self.legacy_path = cache_dir / f"{entry_id}_events.json"
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    async def async_load(self) -> None:
        """Load the stable cache file, migrating the legacy filename if needed."""
        try:
            data = await self.hass.async_add_executor_job(self._read_current_or_legacy)
        except Exception as err:
            _LOGGER.warning("SmartAlarm eventcache lezen mislukt: %s", err)
            data = []

        if isinstance(data, list):
            self._events = self._normalize_and_dedupe(data)

        # Always ensure the new, human-readable filename exists.
        try:
            await self.hass.async_add_executor_job(self._write_file, self._events)
        except Exception as err:
            _LOGGER.warning("SmartAlarm eventcache initialiseren mislukt: %s", err)

        _LOGGER.debug(
            "SmartAlarm eventcache geladen: %d events (%s)",
            len(self._events),
            self.path,
        )

    def _read_current_or_legacy(self) -> Any:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                _LOGGER.warning("SmartAlarm eventcache ongeldig; probeer oude cache")

        if self.legacy_path.exists():
            data = json.loads(self.legacy_path.read_text(encoding="utf-8"))
            # The old file is no longer needed after successful migration.
            try:
                self.legacy_path.unlink()
            except OSError:
                _LOGGER.debug("Oude SmartAlarm eventcache kon niet verwijderd worden")
            return data

        return []

    async def async_merge(self, events: list[dict[str, Any]]) -> bool:
        if not events:
            return False

        merged = self._normalize_and_dedupe(events + self._events)
        if merged == self._events:
            return False

        self._events = merged
        try:
            await self.hass.async_add_executor_job(self._write_file, self._events)
            _LOGGER.debug("SmartAlarm eventcache opgeslagen: %d events", len(self._events))
        except Exception as err:
            _LOGGER.warning("SmartAlarm eventcache schrijven mislukt: %s", err)
        return True

    def _write_file(self, events: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(events, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    @staticmethod
    def _normalize_and_dedupe(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id: dict[str, dict[str, Any]] = {}
        without_id: list[dict[str, Any]] = []

        for event in events:
            if not isinstance(event, dict):
                continue

            item = {
                "id": event.get("id"),
                "created_at": event.get("created_at"),
                "message": event.get("message"),
                "device_id": event.get("device_id"),
                "state": event.get("state"),
            }

            if item["id"] is None:
                without_id.append(item)
            else:
                by_id[str(item["id"])] = item

        result = list(by_id.values()) + without_id
        result.sort(
            key=lambda event: str(event.get("created_at") or ""),
            reverse=True,
        )
        return result[:EVENT_CACHE_MAX]
