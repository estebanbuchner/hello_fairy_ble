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

    async def connect(self):
        try:
            await self.client.connect(timeout=self.timeout)
            self.connected = await self.client.is_connected()
            _LOGGER.info(f"Connected to Hello Fairy: {self.mac}")
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            self.connected = False

    async def disconnect(self):
        await self.client.disconnect()
        self.connected = False

    async def reconnect_if_needed(self):
        if not self.connected:
            _LOGGER.warning("Disconnected. Attempting reconnection...")
            await self.connect()

    async def send_hsv(self, h, s, v):
        """Send HSV command to light."""
        rgb = self.hsv_to_rgb(h, s, v)
        payload = bytearray([0x7e, 0x00, 0x05, 0x03] + rgb + [0xef])
        await self.client.write_gatt_char(CHARACTERISTIC_UUID, payload)
        _LOGGER.debug(f"Sent HSV: {h},{s},{v} → RGB {rgb}")

    async def send_preset(self, preset_id):
        """Send preset effect command."""
        payload = bytearray([0x7e, 0x00, 0x05, 0x04, preset_id, 0x00, 0xef])
        await self.client.write_gatt_char(CHARACTERISTIC_UUID, payload)
        _LOGGER.debug(f"Sent preset ID: {preset_id}")

    async def read_remote_command(self):
        """Read last command from remote (if supported)."""
        try:
            data = await self.client.read_gatt_char(CHARACTERISTIC_UUID)
            self.last_command = data.hex()
            _LOGGER.info(f"Remote command received: {self.last_command}")
        except Exception as e:
            _LOGGER.warning(f"Failed to read remote command: {e}")

    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB (0-255)."""
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
        """Scan for Hello Fairy devices."""
        try:
            devices = await BleakScanner.discover()
            filtered = [d for d in devices if d.name and DEVICE_NAME_PREFIX in d.name]
            if not filtered:
                _LOGGER.warning("No Hello Fairy BLE devices found during scan.")
            return filtered
        except Exception as e:
            _LOGGER.error(f"BLE scan failed: {e}")
            return []
