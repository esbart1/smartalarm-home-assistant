from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN
from .api import SmartAlarmApi


class SmartAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            api = SmartAlarmApi(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            try:
                await api.async_login()
                await api.async_close()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="SmartAlarm", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
