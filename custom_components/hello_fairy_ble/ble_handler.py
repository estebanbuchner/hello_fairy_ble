import asyncio
import logging
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakCharacteristicNotFoundError
from .const import CHARACTERISTIC_UUID, DEVICE_NAME_PREFIX, DEFAULT_TIMEOUT, CHARACTERISTIC_UUID_WRITE, CHARACTERISTIC_UUID_NOTIFY
from typing import Optional, Union, List, Dict, Any
from datetime import datetime
rom bleak_retry_connector import establish_connection

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
        self.last_seen = None
        self.light_ref = None
        self.sensor_ref = None
        # Callback para desconexión
        self.client.set_disconnected_callback(self._on_disconnect)

    async def safe_is_connected(self):
        try:
            estado = self.client.is_connected
            return await estado() if callable(estado) else estado
        except Exception as e:
            _LOGGER.error(f"[safe_is_connected] Error al verificar conexión: {e}")
            return False


    def _on_connect(self):
        self.connected = True

    def _on_disconnect(self, client):
        self.connected = False
        self.notifications_active = False
        _LOGGER.debug(f"Desconectado de {self.mac}")

    @staticmethod
    async def is_device_visible(mac):
        devices = await BleakScanner.discover()
        return any(d.address.lower() == mac.lower() for d in devices)


    async def connect(self):
        try:
            _LOGGER.debug(f"Intentando conectar con {self.mac}")

             # 🔍 Verificar visibilidad BLE antes de conectar
            if not await self.is_device_visible(self.mac):
                _LOGGER.debug(f"{self.mac} no visible en escaneo BLE. Se omite conexión.")
                self.connected = False
                return False

            #await asyncio.wait_for(self.client.connect(timeout=self.timeout), timeout=self.timeout)


            self.client = await establish_connection(  BleakClient(self.mac), self.mac,  max_attempts=3,  timeout=self.timeout, name="HelloFairyBLE" )


            self.connected = await self.safe_is_connected()
            _LOGGER.info(f"Conectado a Hello Fairy: {self.mac} → {self.connected}")

            if self.connected:
                 
                self._on_connect() 

                await self.subscribe_to_notifications()
                await self.send_sync_command()  
                                
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
            _LOGGER.error(f"Timeout al conectar con {self.mac}")
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
        if getattr(self, "_reconnecting", False):
            _LOGGER.debug(f"[reconnect] Ya hay una reconexión en curso para {self.mac}")
            return False
        self._reconnecting = True
        self.reconnect_attempts += 1
        self.last_reconnect_at = datetime.now()

        if not await self.is_device_visible(self.mac):
            _LOGGER.warning(f"[reconnect] Dispositivo {self.mac} no visible en escaneo BLE. Se omite reconexión.")
            self._reconnecting = False
            return False

        for intento in range(3):
            if await self.safe_is_connected():
                self._reconnecting = False
                return True
            _LOGGER.debug(f"Intento de reconexión #{intento+1} para {self.mac}")
            await asyncio.sleep(2 ** intento)
            try:
                await self.connect()
            except Exception as e:
                _LOGGER.warning(f"Falló reconexión #{intento+1}: {e}")

        self._reconnecting = False
        if self.connected:
            _LOGGER.info(f"[reconnect] Reconexión exitosa con {self.mac}")
        else:
            _LOGGER.error(f"[reconnect] Fallaron todos los intentos de reconexión con {self.mac}")
        return self.connected


    async def send_sync_command(self):
        payload = bytearray([0xaa, 0x01, 0x08, 0x00, 0x00, 0x00, 0x02, 0x16, 0x00, 0x43, 0x0e])
        char_uuid = await self.resolve_characteristic()
        if char_uuid:
            await self.client.write_gatt_char(char_uuid, payload, response=False)
            _LOGGER.debug(f"[sync] Comando de sincronización enviado → {payload.hex()}")
        else:
            _LOGGER.error("[sync] No se pudo resolver UUID para sincronización")


    async def resolve_characteristic(self):
        if not self.client or not hasattr(self.client, "services") or not self.client.services:
            _LOGGER.warning(f"[resolve] Cliente BLE no disponible o sin servicios para {self.mac}")
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


    def build_hsv_payload(self, h, s, v):
        # Escalado según protocolo
        hue = int(h)  # 0–360
        sat = int(s * 10)  # 0–100 → 0–1000
        val = int(v * 10)  # 0–100 → 0–1000

        payload = bytearray([
            0xaa, 0x03, 0x07, 0x01,
            (hue >> 8) & 0xFF, hue & 0xFF,
            (sat >> 8) & 0xFF, sat & 0xFF,
            (val >> 8) & 0xFF, val & 0xFF
        ])

        checksum = sum(payload) % 256
        payload.append(checksum)

        return payload


    async def send_hsv(self, h, s, v):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando HSV no enviado.")
            return

        
        payload = self.build_hsv_payload(h, s, v)

            
        dynamic_uuid = await self.resolve_characteristic()
        if dynamic_uuid:
            _LOGGER.warning(f"Usando UUID dinámico: {dynamic_uuid}")
            await self.client.write_gatt_char(dynamic_uuid, payload)
            _LOGGER.debug(f"Comando HSV enviado → {payload.hex()}")
            _LOGGER.debug(f"Sent HSV: {h},{s},{v} ")

        else:
            _LOGGER.error("No se pudo resolver UUID dinámico para HSV")


    async def send_preset(self, preset_id: int, brightness: Optional[int] = None):
        if not await self.safe_is_connected():
            _LOGGER.debug("No conectado. Comando preset no enviado.")
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
            _LOGGER.debug("Agrego suscripcion a notificaciones")
        else:
            _LOGGER.debug("Ignoro suscripcion a notificaciones")



    def _notification_handler(self, sender, data):
        hex_data = data.hex()
        if hex_data != self.last_command:
            _LOGGER.info(f"[notify] Comando nuevo recibido: {hex_data}")
        else:
            _LOGGER.debug(f"[notify] Comando duplicado ignorado: {hex_data}")
        self.last_command = hex_data
        self.last_seen = datetime.now()

        # Decodificación del estado
        if hex_data.startswith("aa01") and hex_data[12:14] == "01":
            self.power_state = True
            _LOGGER.debug(f"[notify] Estado inferido: 'encendido'")
        elif hex_data.startswith("aa01") and hex_data[12:14] == "00":
            self.power_state = False
            _LOGGER.debug(f"[notify] Estado inferido: 'apagado'")
        elif hex_data.startswith("aa01"):
            _LOGGER.debug(f"[notify] {hex_data[11:14]} - {hex_data[0:16]}")

        # Actualización inmediata del estado en Home Assistant
        if self.light_ref:
            self.light_ref._is_on = self.power_state
            self.light_ref.async_write_ha_state()
            _LOGGER.debug(f"[notify] Estado de luz actualizado en HA")

        if self.sensor_ref:
            self.sensor_ref._state = self.last_command
            self.sensor_ref.async_write_ha_state()
            _LOGGER.debug(f"[notify] Estado de sensor actualizado en HA")


    

    async def read_remote_command(self):
        if not await self.safe_is_connected():
            _LOGGER.debug("No conectado. Lectura remota no disponible.")
            return None

        # Ya no intentamos leer directamente
        return getattr(self, "last_command", None)



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


