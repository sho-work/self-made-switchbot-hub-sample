# src/switch_bot/find_by_service_data_and_press.py
import asyncio
from bleak import BleakScanner
from switchbot_api import VirtualSwitchBot
from switchbot_api.bot_types import SwitchBotAction

# 16-bit Service UUID: 0xFD3D → 128-bit形式
FD3D_128 = "0000fd3d-0000-1000-8000-00805f9b34fb"

found = {"addr": None}
ready = asyncio.Event()

def detection_callback(device, advertisement_data):
    # macOSでも advertisement_data.service_data に FD3Dのエントリが来る
    sd = advertisement_data.service_data or {}
    payload = None

    # キーが16bit/128bitどちらで来ても拾えるように両対応
    for k, v in sd.items():
        key = k.lower()
        if key == FD3D_128 or key.endswith("fd3d"):  # 一部環境は 'fd3d' 風に来る
            payload = bytes(v)
            break

    if not payload:
        return

    # Service Data の Byte0 下位7bitが DeviceType（仕様）
    dev_type = payload[0] & 0x7F
    BOT = 0x48  # 'H'
    if dev_type == BOT:
        found["addr"] = device.address  # macOSはUUID形式でOK
        ready.set()

async def main():
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    try:
        try:
            await asyncio.wait_for(ready.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            pass
    finally:
        await scanner.stop()

    if not found["addr"]:
        print("Botが見つかりません。スマホアプリを完全終了→Botを1回押す→再実行してみてください。")
        return

    print("Found Bot:", found["addr"])
    # パスワード未設定想定。設定しているなら password_str="123456" のように渡す
    bot = VirtualSwitchBot(found["addr"])  # or VirtualSwitchBot(found["addr"], password_str="xxxxxx")
    await bot.connect()
    await bot.set_bot_state(SwitchBotAction.PRESS)
    await bot.disconnect()
    print("Pressed successfully!")

def run_bot_press():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
