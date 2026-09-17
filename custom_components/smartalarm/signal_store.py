from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CALIBRATION_SAMPLES, SIGNAL_NORMAL_RATIO, SIGNAL_WARNING_RATIO

_LOGGER = logging.getLogger(__name__)
CALIBRATION_TIMEOUT_MINUTES = 30
SIGNAL_HISTORY_MAX_HOURS = 24 * 30
SIGNAL_TREND_BUCKETS = 6


class SmartAlarmSignalStore:
    """Persistent signal baselines, history and explicit manual calibration."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.path = Path(hass.config.path("custom_components", DOMAIN, "alarm_cache", "smartalarm_signal.json"))
        self._data: dict[str, dict[str, Any]] = {}
        self._load_ok = True

    async def async_load(self) -> None:
        try:
            value = await self.hass.async_add_executor_job(self._read)
            self._data = value if isinstance(value, dict) else {}
            self._load_ok = True
        except Exception as err:
            _LOGGER.warning("SmartAlarm signaalcache lezen mislukt: %s", err)
            self._load_ok = False
            return

        migrated = False
        for item in self._data.values():
            if not isinstance(item, dict):
                continue
            if item.get("calibrating") and item.get("calibration_mode") != "manual":
                item["calibrating"] = False
                item["samples"] = []
                item.pop("calibration_started_at", None)
                item.pop("calibration_timeout_at", None)
                item["calibration_mode"] = None
                migrated = True
            if "normal_ratio" not in item:
                item["normal_ratio"] = SIGNAL_NORMAL_RATIO
                migrated = True
            if "warning_ratio" not in item:
                item["warning_ratio"] = SIGNAL_WARNING_RATIO
                migrated = True
            error = str(item.get("calibration_error") or "").strip()
            if error and error != "Kalibratie mislukt":
                item["calibration_error_detail"] = item.get("calibration_error_detail") or error
                item["calibration_error"] = "Kalibratie mislukt"
                migrated = True
            try:
                normal = float(item["normal_ratio"])
            except (TypeError, ValueError):
                item["normal_ratio"] = SIGNAL_NORMAL_RATIO
                normal = SIGNAL_NORMAL_RATIO
                migrated = True
            try:
                warning = float(item["warning_ratio"])
            except (TypeError, ValueError):
                item["warning_ratio"] = SIGNAL_WARNING_RATIO
                warning = SIGNAL_WARNING_RATIO
                migrated = True
            if warning > normal:
                item["warning_ratio"] = normal
                migrated = True

        if migrated:
            try:
                await self.hass.async_add_executor_job(self._write)
            except Exception as err:
                _LOGGER.warning("SmartAlarm signaalcache migratie schrijven mislukt: %s", err)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("SmartAlarm signaalcache is geen object")
        return value

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    async def _safe_write(self) -> bool:
        if not self._load_ok:
            _LOGGER.warning("SmartAlarm signaalcache niet gewijzigd omdat de vorige read is mislukt")
            return False
        await self.hass.async_add_executor_job(self._write)
        return True

    def get(self, device_id: int) -> dict[str, Any]:
        return dict(self._data.get(str(device_id), {}))

    def reference(self, device_id: int) -> float | None:
        value = self.get(device_id).get("reference")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def calibrated_at(self, device_id: int) -> str | None:
        value = self.get(device_id).get("calibrated_at")
        return str(value) if value else None

    def last_signal_at(self, device_id: int) -> str | None:
        value = self.get(device_id).get("last_signal_at")
        return str(value) if value else None

    def last_signal_value(self, device_id: int) -> float | None:
        value = self.get(device_id).get("last_signal_value")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def is_calibrating(self, device_id: int) -> bool:
        item = self.get(device_id)
        return bool(item.get("calibrating") and item.get("calibration_mode") == "manual")

    def calibration_progress(self, device_id: int) -> tuple[int, int]:
        samples = self.get(device_id).get("samples", [])
        return (len(samples) if isinstance(samples, list) else 0, SIGNAL_CALIBRATION_SAMPLES)

    def normal_ratio(self, device_id: int) -> float:
        try:
            return max(0.50, min(1.00, float(self.get(device_id).get("normal_ratio", SIGNAL_NORMAL_RATIO))))
        except (TypeError, ValueError):
            return SIGNAL_NORMAL_RATIO

    def warning_ratio(self, device_id: int) -> float:
        try:
            warning = max(0.50, min(0.99, float(self.get(device_id).get("warning_ratio", SIGNAL_WARNING_RATIO))))
        except (TypeError, ValueError):
            warning = SIGNAL_WARNING_RATIO
        return min(warning, self.normal_ratio(device_id))

    def normal_threshold(self, device_id: int) -> float | None:
        ref = self.reference(device_id)
        return round(ref * self.normal_ratio(device_id), 1) if ref is not None else None

    def warning_threshold(self, device_id: int) -> float | None:
        ref = self.reference(device_id)
        return round(ref * self.warning_ratio(device_id), 1) if ref is not None else None

    def signal_trend(self, device_id: int) -> dict[str, Any]:
        history = [h for h in self.get(device_id).get("signal_history", []) if isinstance(h, dict) and isinstance(h.get("avg"), (int, float))]
        if len(history) < 2:
            return {"direction": "onvoldoende gegevens", "delta_db": None, "delta_percent": None, "samples": len(history)}
        recent = history[-SIGNAL_TREND_BUCKETS:]
        split = max(0, len(history) - len(recent))
        older = history[max(0, split - SIGNAL_TREND_BUCKETS):split] or history[:max(1, len(history) // 2)]
        old_avg = sum(float(h["avg"]) for h in older) / len(older)
        new_avg = sum(float(h["avg"]) for h in recent) / len(recent)
        delta = round(new_avg - old_avg, 1)
        direction = "dalend" if delta <= -5 else "stijgend" if delta >= 5 else "stabiel"
        return {"direction": direction, "delta_db": delta, "delta_percent": round(delta / old_avg * 100, 1) if old_avg else None, "samples": len(history)}

    async def async_set_normal_ratio(self, device_id: int, value_percent: float) -> None:
        key = str(device_id)
        item = self._data.setdefault(key, {"name": key, "reference": None, "samples": [], "calibrating": False, "normal_ratio": SIGNAL_NORMAL_RATIO, "warning_ratio": SIGNAL_WARNING_RATIO})
        item["normal_ratio"] = max(50.0, min(100.0, float(value_percent))) / 100.0
        item["warning_ratio"] = min(float(item.get("warning_ratio", SIGNAL_WARNING_RATIO)), item["normal_ratio"])
        await self._safe_write()

    async def async_set_warning_ratio(self, device_id: int, value_percent: float) -> None:
        key = str(device_id)
        item = self._data.setdefault(key, {"name": key, "reference": None, "samples": [], "calibrating": False, "normal_ratio": SIGNAL_NORMAL_RATIO, "warning_ratio": SIGNAL_WARNING_RATIO})
        item["warning_ratio"] = min(max(50.0, min(99.0, float(value_percent))) / 100.0, self.normal_ratio(device_id))
        await self._safe_write()

    async def async_start_calibration(self, device_id: int, name: str | None = None) -> None:
        if not self._load_ok:
            raise RuntimeError("SmartAlarm signaalcache is niet beschikbaar")
        key = str(device_id)
        old = dict(self._data.get(key, {}))
        reference = old.get("reference")
        now = dt_util.utcnow()
        item = dict(old)
        item.update({"name": name or old.get("name") or key, "reference": reference, "samples": [], "calibrating": True, "calibration_mode": "manual", "calibration_started_at": now.isoformat(), "calibration_timeout_at": (now + timedelta(minutes=CALIBRATION_TIMEOUT_MINUTES)).isoformat()})
        item.setdefault("normal_ratio", SIGNAL_NORMAL_RATIO)
        item.setdefault("warning_ratio", SIGNAL_WARNING_RATIO)
        self._data[key] = item
        await self._safe_write()

    async def async_process_devices(self, devices: list[dict[str, Any]] | None) -> bool:
        if not self._load_ok:
            return False
        changed = False
        for device in devices or []:
            try:
                device_id = int(device.get("id"))
            except (TypeError, ValueError):
                continue
            key = str(device_id)
            name = str(device.get("name") or key).strip()
            existing_ref = self._data.get(key, {}).get("reference")
            item = self._data.setdefault(key, {"name": name, "reference": None, "samples": [], "calibrating": False, "normal_ratio": SIGNAL_NORMAL_RATIO, "warning_ratio": SIGNAL_WARNING_RATIO})
            if item.get("name") != name:
                item["name"] = name
                changed = True
            if not self.is_calibrating(device_id) and existing_ref is not None:
                item["reference"] = existing_ref

            raw = device.get("signal_strength")
            try:
                signal = float(raw) if raw is not None else None
            except (TypeError, ValueError):
                signal = None
            if signal is not None:
                now = dt_util.utcnow()
                rounded = round(signal, 1)
                item["last_signal_at"] = now.isoformat()
                item["last_signal_value"] = rounded
                bucket_key = now.replace(minute=0, second=0, microsecond=0).isoformat()
                history = item.setdefault("signal_history", [])
                if not isinstance(history, list):
                    history = []
                    item["signal_history"] = history
                if history and history[-1].get("hour") == bucket_key:
                    bucket = history[-1]
                    count = int(bucket.get("count", 0) or 0)
                    avg = float(bucket.get("avg", rounded))
                    bucket["count"] = count + 1
                    bucket["avg"] = round((avg * count + rounded) / (count + 1), 1)
                    bucket["min"] = min(float(bucket.get("min", rounded)), rounded)
                    bucket["max"] = max(float(bucket.get("max", rounded)), rounded)
                else:
                    history.append({"hour": bucket_key, "avg": rounded, "min": rounded, "max": rounded, "count": 1})
                if len(history) > SIGNAL_HISTORY_MAX_HOURS:
                    del history[:-SIGNAL_HISTORY_MAX_HOURS]
                changed = True

            if not self.is_calibrating(device_id) or signal is None:
                continue
            if item.get("calibration_mode") != "manual":
                item["calibrating"] = False
                item["samples"] = []
                changed = True
                continue
            timeout = dt_util.parse_datetime(item.get("calibration_timeout_at")) if item.get("calibration_timeout_at") else None
            if timeout is not None and dt_util.utcnow() >= timeout:
                item["calibrating"] = False
                item["calibration_mode"] = None
                item["samples"] = []
                item.pop("calibration_started_at", None)
                item.pop("calibration_timeout_at", None)
                item["calibration_error"] = "Kalibratie mislukt"
                item["calibration_error_detail"] = "Geen bruikbare signaalmetingen ontvangen"
                changed = True
                continue
            samples = item.setdefault("samples", [])
            if not isinstance(samples, list):
                samples = []
                item["samples"] = samples
            samples.append(signal)
            changed = True
            if len(samples) >= SIGNAL_CALIBRATION_SAMPLES:
                item["reference"] = round(sum(float(v) for v in samples) / len(samples), 1)
                item["samples"] = []
                item["calibrating"] = False
                item["calibration_mode"] = None
                item.pop("calibration_started_at", None)
                item.pop("calibration_timeout_at", None)
                item.pop("calibration_error", None)
                item.pop("calibration_error_detail", None)
                item["calibrated_at"] = dt_util.utcnow().isoformat()
        if changed:
            await self._safe_write()
        return changed

    def status(self, device_id: int, current: float | None) -> str:
        if current is None:
            return "Onbekend - geen recent signaal"
        if self.is_calibrating(device_id):
            done, total = self.calibration_progress(device_id)
            return f"Kalibreren ({done}/{total})"
        reference = self.reference(device_id)
        if reference is None or reference <= 0:
            return "Onbekend - niet gekalibreerd"
        ratio = current / reference
        if ratio >= self.normal_ratio(device_id):
            return "Normaal"
        if ratio >= self.warning_ratio(device_id):
            return "Lager dan normaal"
        return "Sterk verzwakt"
