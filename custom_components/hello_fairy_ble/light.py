import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_EFFECT,
    SUPPORT_BRIGHTNESS, SUPPORT_COLOR, SUPPORT_EFFECT,
    LightEntity
)
from .ble_handler import HelloFairyBLE
from .const import SUPPORTED_EFFECTS

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
        self._device = HelloFairyBLE(mac)

    @property
    def name(self):
        return self._name

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
    def effect_list(self):
        return SUPPORTED_EFFECTS

    @property
    def available(self):
        return self._available

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_EFFECT

    async def async_turn_on(self, **kwargs):
        await self._device.reconnect_if_needed()

        h, s = kwargs.get(ATTR_HS_COLOR, self._hs_color)
        v = kwargs.get(ATTR_BRIGHTNESS, self._brightness) * 100 // 255

        await self._device.send_hsv(h, s, v)
        self._hs_color = (h, s)
        self._brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
        self._is_on = True

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect in SUPPORTED_EFFECTS:
                preset_id = SUPPORTED_EFFECTS.index(effect)
                await self._device.send_preset(preset_id)
                self._effect = effect

    async def async_turn_off(self, **kwargs):
        await self._device.reconnect_if_needed()
        await self._device.send_hsv(0, 0, 0)
        self._is_on = False

    async def async_update(self):
        await self._device.reconnect_if_needed()
        self._available = self._device.connected
