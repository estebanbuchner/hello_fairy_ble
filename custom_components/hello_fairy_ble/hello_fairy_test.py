import asyncio
from hello_fairy_ble import HelloFairyBLE  # Ajustá el import según tu estructura

async def main():
    fairy = HelloFairyBLE("11:11:00:30:4E:14")  # MAC real
    await fairy.connect()
    await fairy.turn_on()
    await asyncio.sleep(2)
    await fairy.turn_off()
    await fairy.disconnect()

asyncio.run(main())
