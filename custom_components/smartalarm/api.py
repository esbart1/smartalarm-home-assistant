from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

from .const import (
    BASE_URL,
    BASE_ID,
    STATE_AWAY,
    STATE_HOME,
    STATE_DISARM,
)


class SmartAlarmApi:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session: aiohttp.ClientSession | None = None
        self.csrf: str | None = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar()
            )

    async def async_login(self):
        await self._ensure_session()

        async with self.session.get(
            f"{BASE_URL}/login",
            headers={
                "User-Agent": "Home Assistant SmartAlarm"
            },
        ) as resp:
            html = await resp.text()

        match = re.search(
            r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        )

        if not match:
            match = re.search(
                r'<input[^>]+name=["\']_token["\'][^>]+value=["\']([^"\']+)',
                html,
                re.I,
            )

        if not match:
            raise RuntimeError("CSRF token not found")

        self.csrf = match.group(1)

        async with self.session.post(
            f"{BASE_URL}/login",
            data={
                "_token": self.csrf,
                "email": self.email,
                "password": self.password,
            },
            headers={
                "User-Agent": "Home Assistant SmartAlarm",
                "Referer": f"{BASE_URL}/login",
            },
            allow_redirects=True,
        ) as resp:
            final_url = str(resp.url)

            if final_url.endswith("/login"):
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

        resp = await self.session.request(
            method,
            url,
            headers=headers,
        )

        if resp.status == 401:
            await resp.release()

            await self.async_login()

            resp = await self.session.request(
                method,
                url,
                headers=headers,
            )

        return resp

    #####################
    async def async_update(self) -> dict[str, Any]:
        """Update alle SmartAlarm gegevens."""

        # ---------------------------------------------------------
        # 1. Bestaande JSON API
        # ---------------------------------------------------------
        resp = await self._request(
            "GET",
            f"{BASE_URL}/json/bases/me?take=12",
        )

        if resp.status >= 400:
            text = await resp.text()
            await resp.release()

            raise RuntimeError(
                f"SmartAlarm HTTP {resp.status}: {text[:200]}"
            )

        data = await resp.json(content_type=None)
        await resp.release()

        # Dit is de bestaande functionaliteit.
        parsed = self._parse(data)

        # ---------------------------------------------------------
        # 2. Apparaten ophalen
        #
        # BELANGRIJK:
        # Een fout hier mag de alarm-integratie NIET stoppen.
        # ---------------------------------------------------------
        try:
            devices = await self._async_get_devices()
            parsed["devices"] = devices

        except Exception as err:
            # Alarm/status blijft gewoon beschikbaar.
            parsed["devices"] = []

            # Alleen loggen; geen exception doorgeven.
            _LOGGER.warning(
                "SmartAlarm apparaten konden niet worden opgehaald: %s",
                err,
            )

        return parsed
######################################

    def _parse(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse de bestaande SmartAlarm JSON response."""

        state = None
        events = []

        def walk(obj):
            nonlocal state, events

            if isinstance(obj, dict):

                if state is None:
                    for key in ("state", "status"):
                        value = obj.get(key)

                        if value in (
                            STATE_AWAY,
                            STATE_HOME,
                            STATE_DISARM,
                        ):
                            state = value

                if isinstance(obj.get("events"), list):
                    events = obj["events"]

                for value in obj.values():
                    walk(value)

            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(data)

        parsed_events = []

        for event in events:
            if isinstance(event, dict):
                parsed_events.append({
                    "id": event.get("id"),
                    "created_at": event.get("created_at"),
                    "message": event.get("message"),
                    "device_id": event.get("device_id"),
                    "state": event.get("state"),
                })

        return {
            "state": state,
            "events": parsed_events,
            "raw": data,
        }

    async def _async_get_devices(self) -> list[dict[str, Any]]:
        """Lees alle apparaten van de SmartAlarm apparatenpagina."""

        await self._ensure_session()

        async with self.session.get(
            f"{BASE_URL}/instellingen/apparaten",
            headers={
                "User-Agent": "Home Assistant SmartAlarm",
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as resp:

            if resp.status >= 400:
                text = await resp.text()

                raise RuntimeError(
                    f"SmartAlarm apparaten HTTP {resp.status}: "
                    f"{text[:200]}"
                )

            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        devices: list[dict[str, Any]] = []

        for link in soup.select(
            'a[href*="/device/"][href*="/edit"]'
        ):
            href = link.get("href")

            if not href:
                continue

            # -----------------------------------------------------
            # Device ID
            #
            # /device/20474/edit
            # -----------------------------------------------------
            parts = href.rstrip("/").split("/")

            device_id = None

            if "device" in parts:
                index = parts.index("device")

                if index + 1 < len(parts):
                    device_id = parts[index + 1]

            if device_id is None:
                continue

            # -----------------------------------------------------
            # Naam
            # -----------------------------------------------------
            name_element = link.select_one(
                ".list-item-text span"
            )

            if name_element:
                name = name_element.get_text(strip=True)
            else:
                name = f"Device {device_id}"

            # -----------------------------------------------------
            # Signaalsterkte
            # -----------------------------------------------------
            signal_element = link.select_one(
                ".signal-strength img[title]"
            )

            signal = None

            if signal_element:
                signal = signal_element.get("title")

            # -----------------------------------------------------
            # Waarschuwing
            # -----------------------------------------------------
            warning = bool(
                link.select_one(
                    ".fa-exclamation-triangle"
                )
            )

            # -----------------------------------------------------
            # Apparaat opslaan
            # -----------------------------------------------------
            devices.append({
                "id": device_id,
                "name": name,
                "url": href,
                "signal": signal,
                "warning": warning,
            })

        return devices

    async def async_set_state(self, state: str):
        """Zet het SmartAlarm aan/uit."""

        if state not in (
            STATE_AWAY,
            STATE_HOME,
            STATE_DISARM,
        ):
            raise ValueError("Invalid SmartAlarm state")

        await self._ensure_session()

        if not self.csrf:
            await self.async_login()

        url = (
            f"{BASE_URL}/bases/"
            f"{BASE_ID}/state/{state}"
        )

        headers = {
            "User-Agent": "Home Assistant SmartAlarm",
            "Accept": "*/*",
            "X-CSRF-TOKEN": self.csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/",
        }

        resp = await self.session.put(
            url,
            headers=headers,
        )

        text = await resp.text()

        if resp.status >= 400:
            raise RuntimeError(
                "SmartAlarm state change failed: "
                f"HTTP {resp.status} {text[:200]}"
            )

        await asyncio.sleep(0.5)

        return await self.async_update()

    async def async_close(self):
        """Sluit de SmartAlarm sessie."""

        if self.session and not self.session.closed:
            await self.session.close()