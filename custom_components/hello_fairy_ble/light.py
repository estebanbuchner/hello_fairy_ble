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
