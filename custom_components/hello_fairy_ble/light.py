import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_EFFECT,
    ColorMode, LightEntityFeature, LightEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .ble_handler import HelloFairyBLE
from .ble_handler import get_ble_instance

from .const import SUPPORTED_EFFECTS, DOMAIN

_LOGGER = logging.getLogger(__name__)

class HelloFairyLight(LightEntity):
    def __init__(self, mac, name):
        self._mac = mac
        self._name = name
        self._is_on = False
        self._brightness = 255
        self._hs_color = (0, 0)
        self._effect = None
        self._available = False
        #self._device = HelloFairyBLE(mac)
        self._device = get_ble_instance(mac)
        self._attr_name = name
        self._attr_supported_color_modes = {ColorMode.HS}
        self._attr_color_mode = ColorMode.HS
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_effect_list = SUPPORTED_EFFECTS
        self._attr_unique_id = f"hello_fairy_{mac.replace(':', '')}"
        self._device.light_ref = self       

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": "Hello Fairy",
            "connections": {("bluetooth", self._mac)},
        }

    @property
    def color_mode(self):
        return ColorMode.HS

    @property
    def supported_color_modes(self):
        return {ColorMode.HS}



    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def effect(self):
        return self._effect

    @property
    def available(self):
        return self._available

    async def async_turn_on(self, **kwargs):
        await self._device.reconnect_if_needed()
        await self._device.send_power(True)
        self._is_on = True

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect in SUPPORTED_EFFECTS:
                preset_id = SUPPORTED_EFFECTS.index(effect) + 1  # ← los presets empiezan en 1
                await self._device.send_preset(preset_id, self._brightness * 100 // 255)
                self._effect = effect
                return

        if ATTR_BRIGHTNESS in kwargs and self._effect:
            preset_id = SUPPORTED_EFFECTS.index(self._effect) + 1
            brightness = kwargs[ATTR_BRIGHTNESS] * 100 // 255
            await self._device.send_preset(preset_id, brightness)
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            return

        # Aplicar color si se especifica
        if ATTR_HS_COLOR in kwargs or ATTR_BRIGHTNESS in kwargs:
            h, s = kwargs.get(ATTR_HS_COLOR, self._hs_color)
            v = kwargs.get(ATTR_BRIGHTNESS, self._brightness) * 100 // 255
            await self._device.send_hsv(h, s, v)
            self._hs_color = (h, s)
            self._brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
            self._effect = None  # ← limpiamos efecto si se aplica color


    async def async_turn_off(self, **kwargs):
        await self._device.reconnect_if_needed()
        await self._device.send_power(False)  # ← nuevo comando directo
        self._is_on = False


    async def async_update(self):
        await self._device.reconnect_if_needed()
        self._available = self._device.connected
        #self._is_on = getattr(self._device, "power_state", False)
        self._is_on = self._device.power_state



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Hello Fairy light from a config entry."""
    data = entry.data
    mac = data.get("mac")
    name = data.get("name", "Hello Fairy")

    if not mac:
        _LOGGER.error("MAC address missing in config entry")
        return

    entity = HelloFairyLight(mac, name)
    await entity.async_update()
    async_add_entities([entity], update_before_add=True)

