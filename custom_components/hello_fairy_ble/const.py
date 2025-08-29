"""Constants for Hello Fairy BLE."""

DOMAIN = "hello_fairy_ble"
DEFAULT_TIMEOUT = 30
CHARACTERISTIC_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"  # UUID BLE para escritura
CHARACTERISTIC_UUID_WRITE = "49535343-8841-43f4-a8d4-ecbe34729bb3"
CHARACTERISTIC_UUID_NOTIFY = "49535343-1e4d-4bd9-ba61-23c647249616"

DEVICE_NAME_PREFIX = "Hello Fairy"

SUPPORTED_EFFECTS = [
    "Rainbow", "Twinkle", "Fireworks", "Ocean", "Blue & White", "Orange Fireworks"
]
