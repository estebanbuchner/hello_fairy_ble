import asyncio
import logging
from bleak import BleakClient, BleakScanner
from .const import CHARACTERISTIC_UUID, DEVICE_NAME_PREFIX, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

class HelloFairyBLE:
    def __init__(self, mac, timeout=DEFAULT_TIMEOUT):
        self.mac = mac
        self.timeout = timeout
        self.client = BleakClient(mac)
        self.connected = False
        self.last_command = None

    # Fase 0.1.0: Helper defensivo para compatibilidad con HA
    async def safe_is_connected(self):
        estado = self.client.is_connected
        return await estado() if callable(estado) else estado

    # Fase 0.1.1: Conexión con timeout y validación de estado
    async def connect(self):
        try:
            _LOGGER.debug(f"Intentando conectar con {self.mac}")
            await asyncio.wait_for(self.client.connect(timeout=self.timeout), timeout=self.timeout)

            self.connected = await self.safe_is_connected()
            _LOGGER.info(f"Conectado a Hello Fairy: {self.mac} → {self.connected}")

            # Fase 0.1.2: Validación de servicios BLE
            if self.connected:
                services = self.client.services
                if not services or not hasattr(services, "services") or len(services.services) == 0:
                    _LOGGER.warning(f"{self.mac} conectado pero sin servicios disponibles")
                    self.connected = False
                    return False

                # Fase 0.1.3: Validación de características
                has_characteristics = any(
                    hasattr(s, "characteristics") and len(s.characteristics) > 0
                    for s in services.services.values()
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

    # Fase 0.2.0: Desconexión segura
    async def disconnect(self):
        try:
            if await self.safe_is_connected():
                await self.client.disconnect()
                _LOGGER.info(f"Desconectado de {self.mac}")
        except Exception:
            _LOGGER.exception(f"Error al desconectar de {self.mac}")
        finally:
            self.connected = False

    # Fase 0.3.0: Reconexión si es necesario
    async def reconnect_if_needed(self):
        if not await self.safe_is_connected():
            _LOGGER.warning("Desconectado. Intentando reconexión...")
            await self.connect()

    # Fase 1.0.0: Envío de comando HSV
    async def send_hsv(self, h, s, v):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando HSV no enviado.")
            return

        rgb = self.hsv_to_rgb(h, s, v)
        payload = bytearray([0x7e, 0x00, 0x05, 0x03] + rgb + [0xef])
        await self.client.write_gatt_char(CHARACTERISTIC_UUID, payload)
        _LOGGER.debug(f"Sent HSV: {h},{s},{v} → RGB {rgb}")

    # Fase 1.1.0: Envío de preset
    async def send_preset(self, preset_id):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Comando preset no enviado.")
            return

        payload = bytearray([0x7e, 0x00, 0x05, 0x04, preset_id, 0x00, 0xef])
        await self.client.write_gatt_char(CHARACTERISTIC_UUID, payload)
        _LOGGER.debug(f"Sent preset ID: {preset_id}")

    # Fase 2.0.0: Lectura de comando remoto
    async def read_remote_command(self):
        if not await self.safe_is_connected():
            _LOGGER.warning("No conectado. Lectura remota no disponible.")
            return

        try:
            data = await self.client.read_gatt_char(CHARACTERISTIC_UUID)
            self.last_command = data.hex()
            _LOGGER.info(f"Remote command received: {self.last_command}")
        except Exception as e:
            _LOGGER.warning(f"Failed to read remote command: {e}")

    # Fase 3.0.0: Conversión HSV → RGB
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

    # Fase 4.0.0: Escaneo BLE con filtro por nombre
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
