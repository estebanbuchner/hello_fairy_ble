from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .ble_handler import HelloFairyBLE
from .ble_handler import get_ble_instance

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)


class HelloFairyRemoteSensor(SensorEntity):
    def __init__(self, mac, name):
        self._mac = mac
        self._name = name
        #self._device = HelloFairyBLE(mac)
        self._device = get_ble_instance(mac)

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

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": "Hello Fairy",
            "connections": {("bluetooth", self._mac)},
        }


class HelloFairyConnectionSensor(SensorEntity):
    def __init__(self, mac, name):
        self._mac = mac
        self._name = name
        #self._device = HelloFairyBLE(mac)
        self._device = get_ble_instance(mac)
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

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": "Hello Fairy",
            "connections": {("bluetooth", self._mac)},
        }




async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    name = entry.data.get("name", "Hello Fairy")

    remote_sensor = HelloFairyRemoteSensor(mac, name)
    connection_sensor = HelloFairyConnectionSensor(mac, name)

    async_add_entities([remote_sensor, connection_sensor])

    # ✅ Encolar la actualización en el loop principal
    def _update_remote_sensor(now):
        hass.async_add_job(remote_sensor.async_schedule_update_ha_state)

    async_track_time_interval(hass, _update_remote_sensor, timedelta(seconds=5))
