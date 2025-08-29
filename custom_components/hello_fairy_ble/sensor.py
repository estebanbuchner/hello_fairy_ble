from homeassistant.components.sensor import SensorEntity
from .hello_fairy_ble import HelloFairyBLE

import logging

_LOGGER = logging.getLogger(__name__)


class HelloFairyRemoteSensor(SensorEntity):
    def __init__(self, mac, name):
        self._mac = mac
        self._name = name
        self._device = HelloFairyBLE(mac)
        self._state = None
        self._attr_name = f"{name} Remote Command"
        self._attr_unique_id = f"hello_fairy_remote_{mac.replace(':', '')}"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        await self._device.reconnect_if_needed()
        command = await self._device.read_remote_command()
        if command:
            self._state = command

class HelloFairyConnectionSensor(SensorEntity):
    def __init__(self, mac, name):
        self._mac = mac
        self._name = name
        self._device = HelloFairyBLE(mac)
        self._state = "unknown"
        self._attr_name = f"{name} Connection"
        self._attr_unique_id = f"hello_fairy_connection_{mac.replace(':', '')}"
        self._attr_icon = "mdi:bluetooth-connect"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        try:
            connected = await self._device.safe_is_connected()
            self._state = "connected" if connected else "disconnected"
        except Exception as e:
            _LOGGER.warning(f"Error al verificar conexión BLE: {e}")
            self._state = "error"


async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    name = entry.data.get("name", "Hello Fairy")

    entities = [
        HelloFairyRemoteSensor(mac, name),
        HelloFairyConnectionSensor(mac, name),
    ]

    async_add_entities(entities)

