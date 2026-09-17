from __future__ import annotations

import asyncio
import json
import logging
import re
from html import unescape
from typing import Any

import aiohttp

from .const import BASE_ID, BASE_URL, STATE_AWAY, STATE_DISARM, STATE_HOME

_LOGGER = logging.getLogger(__name__)


class SmartAlarmApi:
    """Minimal async client for the SmartAlarm web application/API."""

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password
        self.session: aiohttp.ClientSession | None = None
        self.csrf: str | None = None

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
            raise RuntimeError("CSRF token not found")
        self.csrf = match.group(1)
        async with self.session.post(
            f"{BASE_URL}/login",
            data={"_token": self.csrf, "email": self.email, "password": self.password},
            headers={"User-Agent": "Home Assistant SmartAlarm", "Referer": f"{BASE_URL}/login"},
            allow_redirects=True,
        ) as resp:
            if str(resp.url).endswith("/login"):
                raise RuntimeError("SmartAlarm login failed")

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
            await self.async_login()
            headers["X-CSRF-TOKEN"] = self.csrf or ""
            resp = await self.session.request(method, url, headers=headers)
        return resp

    async def async_update(self) -> dict[str, Any]:
        resp = await self._request("GET", f"{BASE_URL}/json/bases/me?take=12")
        try:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"SmartAlarm HTTP {resp.status}: {text[:200]}")
            return self._parse(await resp.json(content_type=None))
        finally:
            await resp.release()

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

    def _parse(self, data: dict[str, Any]) -> dict[str, Any]:
        state = None
        events: list[dict[str, Any]] = []

        def walk(obj: Any) -> None:
            nonlocal state, events
            if isinstance(obj, dict):
                if state is None:
                    for key in ("state", "status"):
                        value = obj.get(key)
                        if value in (STATE_AWAY, STATE_HOME, STATE_DISARM):
                            state = value
                if isinstance(obj.get("events"), list):
                    events = obj["events"]
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
        return {"state": state, "events": clean_events, "raw": data}

    async def async_set_state(self, state: str) -> dict[str, Any]:
        if state not in (STATE_AWAY, STATE_HOME, STATE_DISARM):
            raise ValueError("Invalid SmartAlarm state")
        await self._ensure_session()
        if not self.csrf:
            await self.async_login()
        resp = await self.session.put(
            f"{BASE_URL}/bases/{BASE_ID}/state/{state}",
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
