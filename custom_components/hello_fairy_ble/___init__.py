"""Hello Fairy BLE integration."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import async_add_entities
from .light import HelloFairyLight

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Hello Fairy BLE integration."""
    _LOGGER.info("Setting up Hello Fairy BLE")
    # Aquí podrías cargar desde YAML si querés soporte legacy
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    mac = entry.data["mac"]
    name = entry.data["name"]
    async_add_entities([HelloFairyLight(mac, name)])
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return True
