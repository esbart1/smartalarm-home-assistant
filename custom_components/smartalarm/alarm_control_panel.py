from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_AWAY, STATE_HOME, STATE_DISARM


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartAlarmAlarmPanel(data["coordinator"], data["api"], entry)])


class SmartAlarmAlarmPanel(CoordinatorEntity, AlarmControlPanelEntity):
    _attr_name = "SmartAlarm alarm"
    _attr_icon = "mdi:shield-home"
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
    )

    def __init__(self, coordinator, api, entry):
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_alarm"

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        state = self.coordinator.data.get("state")
        return {
            STATE_AWAY: AlarmControlPanelState.ARMED_AWAY,
            STATE_HOME: AlarmControlPanelState.ARMED_HOME,
            STATE_DISARM: AlarmControlPanelState.DISARMED,
        }.get(state)

    async def async_alarm_arm_away(self, code=None):
        await self.api.async_set_state(STATE_AWAY)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_home(self, code=None):
        await self.api.async_set_state(STATE_HOME)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code=None):
        await self.api.async_set_state(STATE_DISARM)
        await self.coordinator.async_request_refresh()
