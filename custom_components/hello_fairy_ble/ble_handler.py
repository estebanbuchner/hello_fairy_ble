import asyncio
import logging
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakCharacteristicNotFoundError
from .const import CHARACTERISTIC_UUID, DEVICE_NAME_PREFIX, DEFAULT_TIMEOUT, CHARACTERISTIC_UUID_WRITE, CHARACTERISTIC_UUID_NOTIFY
from typing import Optional, Union, List, Dict, Any
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


_ble_instances = {}

def get_ble_instance(mac):
    if mac not in _ble_instances:
        _ble_instances[mac] = HelloFairyBLE(mac)
    return _ble_instances[mac]


class HelloFairyBLE:
    def __init__(self, mac, timeout=DEFAULT_TIMEOUT):
        self.mac = mac
        self.timeout = timeout
        self.client = BleakClient(mac)
        self.connected = False
        self.last_command = None
        self.notifications_active = False
        self.reconnect_attempts = 0

        self.power_state = None


        # Callback para desconexión
        self.client.set_disconnected_callback(self._on_disconnect)

    async def safe_is_connected(self):
        try:
            estado = self.client.is_connected
            return await estado() if callable(estado) else estado
        except Exception as e:
            _LOGGER.warning(f"[safe_is_connected] Error al verificar conexión: {e}")
            return False


    def _on_connect(self):
        self.connected = True

    def _on_disconnect(self, client):
        self.connected = False
        self.notifications_active = False
        _LOGGER.warning(f"Desconectado de {self.mac}")

    @staticmethod
    async def is_device_visible(mac):
        devices = await BleakScanner.discover()
        return any(d.address.lower() == mac.lower() for d in devices)


    async def connect(self):
        try:
            _LOGGER.debug(f"Intentando conectar con {self.mac}")

             # 🔍 Verificar visibilidad BLE antes de conectar
            if not await self.is_device_visible(self.mac):
                _LOGGER.warning(f"{self.mac} no visible en escaneo BLE. Se omite conexión.")
                self.connected = False
                return False

            await asyncio.wait_for(self.client.connect(timeout=self.timeout), timeout=self.timeout)

            self.connected = await self.safe_is_connected()
            _LOGGER.info(f"Conectado a Hello Fairy: {self.mac} → {self.connected}")

            if self.connected:
                 
                self._on_connect() 

                await self.subscribe_to_notifications()
                                
                # ✅ Acceso directo a servicios sin await
                services = self.client.services

                for service in self.client.services:
                    _LOGGER.debug(f"Servicio: {service.uuid}")
                    for char in service.characteristics:
                        _LOGGER.debug(f"  Char: {char.uuid} → {char.properties}")

                has_characteristics = any(
                    hasattr(s, "characteristics") and len(s.characteristics) > 0
                    for s in self.client.services
                )
                if not has_characteristics:
                    _LOGGER.warning(f"{self.mac} conectado pero sin características en los servicios")
                    self.connected = False
                    return False

            return self.connected

        except asyncio.TimeoutError:
            _LOGGER.warning(f"Timeout al conectar con {self.mac}")
            self.connected = False
            return False

        except Exception:
            _LOGGER.exception(f"Error general al conectar con {self.mac}")
            self.connected = False
            return False

    async def disconnect(self):
        try:
            if await self.safe_is_connected():
                await self.client.disconnect()
                _LOGGER.info(f"Desconectado de {self.mac}")
        except Exception:
            _LOGGER.exception(f"Error al desconectar de {self.mac}")
        finally:
            self.connected = False

    async def reconnect_if_needed(self):
        self.reconnect_attempts += 1
        self.last_reconnect_at = datetime.now()

        for intento in range(3):
            if await self.safe_is_connected():
                return True
            _LOGGER.warning(f"Intento de reconexión #{intento+1} para {self.mac}")
            await asyncio.sleep(2 ** intento)  # 1s, 2s, 4s
            try:
                await self.connect()
            except Exception as e:
                _LOGGER.warning(f"Falló reconexión #{intento+1}: {e}")
        return False



    async def resolve_characteristic(self):
        if not self.client.services:
            _LOGGER.warning(f"No hay servicios disponibles para {self.mac}")
            return None

        try:
            for service in self.client.services:
                for char in service.characteristics:
                    if "write" in char.properties:
                        _LOGGER.debug(f"Característica candidata: {char.uuid}")
                        return char.uuid
        except Exception:
            _LOGGER.exception("Error al resolver característica BLE")
        return None

    async def send_hsv(self, h, s, v):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando HSV no enviado.")
            return

        rgb = self.hsv_to_rgb(h, s, v)
        payload = bytearray([0x7e, 0x00, 0x05, 0x03] + rgb + [0xef])

        try:
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, payload)
        except BleakCharacteristicNotFoundError:
            _LOGGER.warning(f"UUID fijo falló: {CHARACTERISTIC_UUID}")
            dynamic_uuid = await self.resolve_characteristic()
            if dynamic_uuid:
                _LOGGER.warning(f"Usando UUID dinámico: {dynamic_uuid}")
                await self.client.write_gatt_char(dynamic_uuid, payload)
            else:
                _LOGGER.error("No se pudo resolver UUID dinámico para HSV")
        else:
            _LOGGER.debug(f"Sent HSV: {h},{s},{v} → RGB {rgb}")

    async def send_preset(self, preset_id: int, brightness: Optional[int] = None):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando preset no enviado.")
            return

        # Si no se especifica brillo, usar el último conocido
        brightness = brightness or self._brightness * 100 // 255
        brightness = max(1, min(brightness, 100))  # Clamp
        b_scaled = brightness * 10  # Escalado a 0–1000

        payload = bytearray([
            0xaa, 0x03, 0x04, 0x02,
            preset_id & 0xFF,
            (b_scaled >> 8) & 0xFF,
            b_scaled & 0xFF,
            0x00  # checksum placeholder
        ])
        payload[-1] = sum(payload[:-1]) % 256  # checksum

        char_uuid = await self.resolve_characteristic()
        if char_uuid:
            await self.client.write_gatt_char(char_uuid, payload, response=False)
            _LOGGER.debug(f"Comando preset enviado → {payload.hex()}")
        else:
            _LOGGER.error("No se pudo resolver UUID para preset")

    async def subscribe_to_notifications(self):
        if not self.notifications_active:
            await self.client.start_notify(CHARACTERISTIC_UUID_NOTIFY, self._notification_handler)
            self.notifications_active = True
            _LOGGER.info("Agrego suscripcion a notificaciones")
        else:
            _LOGGER.warning("Ignoro suscripcion a notificaciones")



    def _notification_handler(self, sender, data):
        hex_data = data.hex()
        if hex_data != self.last_command:
            _LOGGER.debug(f"[notify] Comando nuevo recibido: {hex_data}")
        else:
            _LOGGER.debug(f"[notify] Comando duplicado ignorado: {hex_data}")
        self.last_command = hex_data
    
        self.last_seen = datetime.now()


        if hex_data.startswith("aa01") and hex_data[12:14] == "01":
            self.power_state = True
            _LOGGER.debug(f"[notify] Estado inferido: 'encendido' ")
        elif hex_data.startswith("aa01") and hex_data[12:14] == "00":
            self.power_state = False
            _LOGGER.debug(f"[notify] Estado inferido: 'apagado' ")
        elif hex_data.startswith("aa01"):
            _LOGGER.debug(f"[notify] {hex_data[11:14]} - {hex_data[0:16]} ")

    

    async def read_remote_command(self):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Lectura remota no disponible.")
            return None

        # Ya no intentamos leer directamente
        return getattr(self, "last_command", None)



    def hsv_to_rgb(self, h, s, v):
        h = float(h)
        s = float(s) / 100
        v = float(v) / 100
        i = int(h / 60) % 6
        f = (h / 60) - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        rgb_map = {
            0: (v, t, p),
            1: (q, v, p),
            2: (p, v, t),
            3: (p, q, v),
            4: (t, p, v),
            5: (v, p, q),
        }
        r, g, b = rgb_map[i]
        return [int(r * 255), int(g * 255), int(b * 255)]

    @staticmethod
    async def discover_devices():
        try:
            devices = await BleakScanner.discover()
            for d in devices:
                _LOGGER.warning(f"BLE detectado: {d.address} - {d.name}")

            filtered = [
                d for d in devices
                if d.name and DEVICE_NAME_PREFIX.lower() in d.name.lower()
            ]

            if not filtered:
                _LOGGER.warning("No Hello Fairy BLE devices found during scan.")

            return filtered
        except Exception as e:
            _LOGGER.error(f"BLE scan failed: {e}")
            return []
        
    async def send_power(self, state: bool):
        """Enciende o apaga la luz con comando directo."""
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando de encendido/apagado no enviado.")
            return

        self.power_state = state

        payload = bytearray([0xaa, 0x02, 0x01, 0x01 if state else 0x00, 0xae if state else 0xad])
        char_uuid = await self.resolve_characteristic()
        if char_uuid:
            await self.client.write_gatt_char(char_uuid, payload, response=False)
            _LOGGER.debug(f"Comando {'encendido' if state else 'apagado'} enviado → {payload.hex()}")
        else:
            _LOGGER.error("No se pudo resolver UUID para comando de encendido/apagado")


