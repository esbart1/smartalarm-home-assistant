from __future__ import annotations

import asyncio
import json
import logging
import re
from html import unescape
from typing import Any

import aiohttp

from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import BASE_URL, STATE_AWAY, STATE_DISARM, STATE_HOME

_LOGGER = logging.getLogger(__name__)


class SmartAlarmAuthError(Exception):
    """Raised when SmartAlarm rejects the configured credentials."""



class SmartAlarmApi:
    """Minimal async client for the SmartAlarm web application/API."""

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password
        self.session: aiohttp.ClientSession | None = None
        self.csrf: str | None = None
        self.base_id: str | None = None

    async def _ensure_session(self) -> None:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(),
                timeout=aiohttp.ClientTimeout(total=20, connect=10),
            )

    async def async_login(self) -> None:
        await self._ensure_session()
        async with self.session.get(
            f"{BASE_URL}/login",
            headers={"User-Agent": "Home Assistant SmartAlarm"},
        ) as resp:
            html = await resp.text()
        match = re.search(
            r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        ) or re.search(
            r'<input[^>]+name=["\']_token["\'][^>]+value=["\']([^"\']+)',
            html,
            re.I,
        )
        if not match:
            raise RuntimeError("SmartAlarm loginpagina of CSRF-token niet gevonden")
        self.csrf = match.group(1)
        async with self.session.post(
            f"{BASE_URL}/login",
            data={"_token": self.csrf, "email": self.email, "password": self.password},
            headers={"User-Agent": "Home Assistant SmartAlarm", "Referer": f"{BASE_URL}/login"},
            allow_redirects=True,
        ) as resp:
            if resp.status in (401, 403) or str(resp.url).rstrip("/").endswith("/login"):
                raise SmartAlarmAuthError("SmartAlarm heeft de inloggegevens geweigerd")

    async def _request(self, method: str, url: str):
        await self._ensure_session()
        headers = {
            "User-Agent": "Home Assistant SmartAlarm",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        if self.csrf:
            headers["X-CSRF-TOKEN"] = self.csrf
        resp = await self.session.request(method, url, headers=headers)
        if resp.status in (401, 419):
            await resp.release()
            try:
                await self.async_login()
            except SmartAlarmAuthError as err:
                raise ConfigEntryAuthFailed("SmartAlarm inloggegevens ongeldig; stel de integratie opnieuw in") from err
            headers["X-CSRF-TOKEN"] = self.csrf or ""
            resp = await self.session.request(method, url, headers=headers)
            if resp.status in (401, 419):
                await resp.release()
                raise RuntimeError(f"SmartAlarm sessie kon niet worden vernieuwd (HTTP {resp.status})")
        return resp

    async def async_update(self) -> dict[str, Any]:
        resp = await self._request("GET", f"{BASE_URL}/json/bases/me?take=12")
        try:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"SmartAlarm HTTP {resp.status}: {text[:200]}")
            raw_data = await resp.json(content_type=None)
            parsed = self._parse(raw_data)
            base_id = self._extract_base_id(raw_data)
            if base_id is None:
                # Some SmartAlarm accounts return a response shape that does not
                # expose the base as a `bases` collection. The authenticated
                # dashboard contains the same base ID in its alarm element.
                base_id = await self._async_get_base_id_from_dashboard()
            if base_id is not None:
                self.base_id = str(base_id)
            elif self.base_id is None:
                raise RuntimeError(
                    "SmartAlarm basisstation-ID niet gevonden in /json/bases/me "
                    "of op de bedieningspagina"
                )
            parsed["base_id"] = self.base_id
            return parsed
        finally:
            await resp.release()

    async def _async_get_base_id_from_dashboard(self) -> str | None:
        """Read the base ID from the authenticated dashboard's alarm element."""
        await self._ensure_session()
        async with self.session.get(
            f"{BASE_URL}/",
            headers={"User-Agent": "Home Assistant SmartAlarm", "Accept": "text/html"},
        ) as resp:
            if resp.status >= 400:
                _LOGGER.debug("SmartAlarm dashboard ophalen voor basisstation-ID: HTTP %s", resp.status)
                return None
            html = await resp.text()
        # The dashboard supplied by SmartAlarm uses e.g. class="alarm" data-id="1429".
        match = re.search(
            r'<[^>]*class=["\'][^"\']*\balarm\b[^"\']*["\'][^>]*\bdata-id=["\'](\d+)["\']',
            html,
            re.I,
        )
        if not match:
            # Attribute order can differ in generated HTML.
            match = re.search(
                r'<[^>]*\bdata-id=["\'](\d+)["\'][^>]*class=["\'][^"\']*\balarm\b[^"\']*["\']',
                html,
                re.I,
            )
        return match.group(1) if match else None

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Read the full authenticated SmartAlarm device inventory."""
        resp = await self._request("GET", f"{BASE_URL}/instellingen/apparaten")
        try:
            status = resp.status
            text = await resp.text()
        finally:
            await resp.release()
        if status >= 400:
            raise RuntimeError(f"SmartAlarm devices HTTP {status}: {text[:200]}")

        devices: list[dict[str, Any]] = []
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            parsed = None

        def add_device(device: dict[str, Any]) -> None:
            device_id = device.get("id")
            name = device.get("name")
            if device_id is None or not name:
                return
            clean = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(name))).strip())
            if not clean:
                return
            if "afstandsbediening" in clean.casefold():
                return
            try:
                device_id = int(device_id)
            except (TypeError, ValueError):
                return
            devices.append(
                {
                    "id": device_id,
                    "name": clean,
                    "signal_strength": device.get("rssi", device.get("signal_strength")),
                    "state": device.get("state"),
                    "device_type_id": device.get("device_type_id"),
                }
            )

        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                if isinstance(obj.get("devices"), list):
                    for item in obj["devices"]:
                        if isinstance(item, dict):
                            add_device(item)
                else:
                    for value in obj.values():
                        walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        if parsed is not None:
            walk(parsed)
        else:
            # Parse one complete <a>...</a> device block at a time. This is
            # important for devices such as 04 Voordeur Vertraagd that can
            # have no signal image of their own; never borrow the signal from
            # the preceding or following device.
            anchor_pattern = re.compile(
                r'<a\b[^>]*href=["\'][^"\']*/device/(\d+)/edit[^"\']*["\'][^>]*>.*?</a>',
                re.I | re.S,
            )
            for anchor in anchor_pattern.finditer(text):
                device_id = int(anchor.group(1))
                block = anchor.group(0)
                name_match = re.search(
                    r"list-item-text[^>]*>.*?<span[^>]*>\s*(.*?)\s*</span>",
                    block,
                    re.I | re.S,
                )
                signal_match = re.search(
                    r'<img[^>]+(?:title|alt)=["\']\s*([0-9]+(?:\.[0-9]+)?)\s*dB["\']',
                    block,
                    re.I,
                )
                add_device(
                    {
                        "id": device_id,
                        "name": name_match.group(1) if name_match else f"Device {device_id}",
                        "signal_strength": float(signal_match.group(1)) if signal_match else None,
                    }
                )

        unique: list[dict[str, Any]] = []
        seen: set[int] = set()
        for device in devices:
            if device["id"] not in seen:
                seen.add(device["id"])
                unique.append(device)
        _LOGGER.debug("SmartAlarm: %d apparaten gevonden", len(unique))
        return unique

    @staticmethod
    def _extract_base_id(data: Any) -> str | None:
        """Extract the base ID from the authenticated /json/bases/me response.

        Prefer objects inside a bases collection to avoid confusing sensor IDs
        with the base ID. Support common API response wrappers.
        """
        candidates: list[Any] = []

        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.casefold() in {"bases", "base", "alarm_base", "alarmbase"}:
                        if isinstance(value, dict):
                            candidates.append(value)
                        elif isinstance(value, list):
                            candidates.extend(item for item in value if isinstance(item, dict))
                    if isinstance(value, (dict, list)):
                        walk(value)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(data)
        if isinstance(data, list):
            candidates.extend(item for item in data if isinstance(item, dict))
        # If the response itself (or a common `data` wrapper) is a single
        # base object, accept its ID. Do not search arbitrary nested objects,
        # because those may be sensor/device IDs rather than the base ID.
        if isinstance(data, dict) and not candidates:
            if data.get("id") is not None:
                candidates.append(data)
            wrapped = data.get("data")
            if isinstance(wrapped, dict) and wrapped.get("id") is not None:
                candidates.append(wrapped)
            elif isinstance(wrapped, list):
                candidates.extend(item for item in wrapped if isinstance(item, dict))
        for item in candidates:
            value = item.get("id", item.get("base_id", item.get("baseId")))
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    def _parse(self, data: dict[str, Any]) -> dict[str, Any]:
        state = None
        events: list[dict[str, Any]] = []
        devices: list[dict[str, Any]] = []

        def add_devices(items: Any) -> None:
            if not isinstance(items, list):
                return
            for device in items:
                if not isinstance(device, dict) or device.get("id") is None:
                    continue
                devices.append({
                    "id": device.get("id"),
                    "name": device.get("name"),
                    "signal_strength": device.get("rssi", device.get("signal_strength")),
                    "state": device.get("state"),
                    "device_type_id": device.get("device_type_id"),
                })

        def walk(obj: Any) -> None:
            nonlocal state, events
            if isinstance(obj, dict):
                if state is None:
                    for key in ("state", "status"):
                        value = obj.get(key)
                        if value in (STATE_AWAY, STATE_HOME, STATE_DISARM):
                            state = value
                if isinstance(obj.get("events"), list):
                    events.extend(obj["events"])
                if isinstance(obj.get("devices"), list):
                    add_devices(obj["devices"])
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(data)

        clean_events = [
            {
                "id": event.get("id"),
                "created_at": event.get("created_at"),
                "message": event.get("message"),
                "device_id": event.get("device_id"),
                "state": event.get("state"),
            }
            for event in events
            if isinstance(event, dict)
        ]

        unique_devices: dict[str, dict[str, Any]] = {}
        for device in devices:
            unique_devices[str(device["id"])] = device

        return {
            "state": state,
            "events": clean_events,
            "devices": list(unique_devices.values()),
            "raw": data,
        }

    async def async_set_state(self, state: str) -> dict[str, Any]:
        if state not in (STATE_AWAY, STATE_HOME, STATE_DISARM):
            raise ValueError("Invalid SmartAlarm state")
        await self._ensure_session()
        if not self.csrf:
            await self.async_login()
        if not self.base_id:
            await self.async_update()
        if not self.base_id:
            raise RuntimeError("SmartAlarm basisstation-ID is niet bekend")
        resp = await self.session.put(
            f"{BASE_URL}/bases/{self.base_id}/state/{state}",
            headers={
                "User-Agent": "Home Assistant SmartAlarm",
                "Accept": "*/*",
                "X-CSRF-TOKEN": self.csrf or "",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE_URL,
                "Referer": f"{BASE_URL}/",
            },
        )
        try:
            text = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(f"SmartAlarm state change failed: HTTP {resp.status} {text[:200]}")
        finally:
            await resp.release()
        await asyncio.sleep(0.5)
        return await self.async_update()

    async def async_close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
