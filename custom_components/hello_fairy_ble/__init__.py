"""Hello Fairy BLE integration."""
import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_flow



from .light import HelloFairyLight
from .ble_handler import HelloFairyBLE
from .ble_handler import get_ble_instance

from .sensor import HelloFairyRemoteSensor
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Hello Fairy BLE integration."""
    _LOGGER.info("Setting up Hello Fairy BLE")
    # Aquí podrías cargar desde YAML si querés soporte legacy
    return True





async def handle_send_raw_command(call):
    mac = call.data["mac"]
    raw = call.data["raw"]

    try:
        # Convertir string a bytearray
        parts = [int(x.strip(), 16) for x in raw.split(",")]
        payload = bytearray(parts)
        payload[-1] = sum(payload[:-1]) % 256  # checksum

        device = get_ble_instance(mac)
        await device.reconnect_if_needed()

        char_uuid = await device.resolve_characteristic()
        if char_uuid:
            await device.client.write_gatt_char(char_uuid, payload, response=False)
            _LOGGER.info(f"Comando raw enviado → {payload.hex()}")
        else:
            _LOGGER.error("No se pudo resolver UUID para comando raw")

    except Exception as e:
        _LOGGER.exception(f"Error al enviar comando raw: {e}")



async def handle_send_preset_command(call):
    mac = call.data["mac"]
    preset_id = int(call.data["preset_id"])
    brightness = int(call.data.get("brightness", 100))  # default: 100%

    try:
        # Escalar brillo a rango 0–1000
        b_scaled = max(1, min(brightness, 100)) * 10
        hi = (b_scaled >> 8) & 0xFF
        lo = b_scaled & 0xFF

        # Construir payload
        payload = bytearray([
            0xaa, 0x03, 0x04, 0x02,
            preset_id & 0xFF,
            hi,
            lo,
            0x00  # checksum placeholder
        ])
        payload[-1] = sum(payload[:-1]) % 256  # checksum

        device = get_ble_instance(mac)
        await device.reconnect_if_needed()

        char_uuid = await device.resolve_characteristic()
        if char_uuid:
            await device.client.write_gatt_char(char_uuid, payload, response=False)
            _LOGGER.info(f"Comando preset enviado → {payload.hex()}")
        else:
            _LOGGER.error("No se pudo resolver UUID para comando preset")

    except Exception as e:
        _LOGGER.exception(f"Error al enviar comando preset: {e}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data


    await hass.config_entries.async_forward_entry_setups(entry, ["light", "sensor"])

    hass.services.async_register(DOMAIN, "send_raw_command", handle_send_raw_command)
    hass.services.async_register(DOMAIN, "send_preset_command", handle_send_preset_command)


   



    return True



async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return True


