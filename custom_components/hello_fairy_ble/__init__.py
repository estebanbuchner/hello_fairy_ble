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




# ⬇️ Función de servicio definida fuera
async def async_test_light_service(call):
    mac = call.data.get("mac", "11:11:00:30:4E:14")
    #device = HelloFairyBLE(mac)
    device = get_ble_instance(mac)

    if await device.connect():

     
        await device.connect()
        await device.turn_on()
        await asyncio.sleep(2)

        await device.send_preset(41, brightness=80)  # Blue & White
        await asyncio.sleep(10)
        
        await device.send_preset(58, brightness=100) # Orange Fireworks
        await asyncio.sleep(10)

        await device.turn_off()
        await device.disconnect()


    else:
        _LOGGER.warning(f"No se pudo conectar con {mac}")


async def handle_send_raw_command(call):
    mac = call.data["mac"]
    raw = call.data["raw"]

    try:
        # Convertir string a bytearray
        parts = [int(x.strip(), 16) for x in raw.split(",")]
        payload = bytearray(parts)

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data


    await hass.config_entries.async_forward_entry_setups(entry, ["light", "sensor"])

    hass.services.async_register(DOMAIN, "test_light", async_test_light_service)
    hass.services.async_register(DOMAIN, "send_raw_command", handle_send_raw_command)


   



    return True



async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return True


