import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEVICE_NAME_PREFIX
from .ble_handler import HelloFairyBLE

_LOGGER = logging.getLogger(__name__)

class HelloFairyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            mac = user_input["mac"]
            name = user_input["name"]

            device = HelloFairyBLE(mac)
            await device.connect()
            if not device.connected:
                errors["base"] = "cannot_connect"
            else:
                await device.disconnect()
                return self.async_create_entry(title=name, data=user_input)

        devices = await HelloFairyBLE.discover_devices()
        choices = {d.address: d.name for d in devices if DEVICE_NAME_PREFIX in d.name}

        schema = vol.Schema({
            vol.Required("mac"): vol.In(choices),
            vol.Required("name"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    ...

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
