from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN
from .api import SmartAlarmApi, SmartAlarmAuthError


class SmartAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            api = SmartAlarmApi(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            try:
                await api.async_login()
                result = await api.async_update()
                if not result.get("base_id"):
                    raise RuntimeError("SmartAlarm basisstation-ID ontbreekt")
            except SmartAlarmAuthError:
                errors["base"] = "invalid_auth"
            except (OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].strip().casefold())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="SmartAlarm", data=user_input)
            finally:
                await api.async_close()

        schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._reauth_entry
        if user_input:
            api = SmartAlarmApi(entry.data[CONF_EMAIL], user_input[CONF_PASSWORD])
            try:
                await api.async_login()
                result = await api.async_update()
                if not result.get("base_id"):
                    raise RuntimeError("SmartAlarm basisstation-ID ontbreekt")
            except SmartAlarmAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            finally:
                await api.async_close()

        schema = vol.Schema({vol.Required(CONF_PASSWORD): str})
        return self.async_show_form(step_id="reauth_confirm", data_schema=schema, errors=errors,
                                   description_placeholders={"email": entry.data[CONF_EMAIL]})
