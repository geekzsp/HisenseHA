# config_flow.py

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_WIFI_ID, CONF_DEVICE_ID, CONF_TOKEN


def vol_schema(schema: dict, defaults: dict | None) -> vol.Schema:
    if defaults:
        for key in schema:
            if (value := defaults.get(key.schema)) is not None:
                key.default = vol.default_factory(value)
    return vol.Schema(schema)


class HisenseACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Here you could add code to validate the input, such as attempting to connect to the AC
            # For simplicity, we'll assume the input is valid
            return self.async_create_entry(title="Hisense Smart Control", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_WIFI_ID): str,
                vol.Required(CONF_DEVICE_ID, ): str,
                vol.Required(CONF_TOKEN): str,
            }),
            description_placeholders={
                "wifi_id_hint": "WiFi ID here",
                "device_id_hint": "Device ID here",
                "token_hint": "Token here",
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry
        self.config = dict(config_entry.data)

    async def async_step_init(self, user_input: dict = None):
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict = None):
        if user_input:
            # self.config_entry.data.update(user_input)
            self.config.update(user_input)
            # self.options.update(user_input)
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.config
            )
            return self.async_create_entry(title="Hisense Smart Control", data=user_input)

        defaults = self.config_entry.data.copy()
        data = vol_schema(
            {
                vol.Required(CONF_WIFI_ID): str,
                vol.Required(CONF_DEVICE_ID, ): str,
                vol.Required(CONF_TOKEN): str,
            },
            defaults,
        )
        description_placeholders = {
            "wifi_id_hint": "WiFi ID here",
            "device_id_hint": "Device ID here",
            "token_hint": "Token here",
        }
        return self.async_show_form(step_id="user", data_schema=data, description_placeholders=description_placeholders)
