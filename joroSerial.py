import websockets
import uuid
import json
import asyncio
import serial
import time
import pygame
import threading

# WebSocketサーバーのURL
SERVER_URL = "ws://localhost:3210"
# SERVER_URL = "wss://project-yggdrasill-backend.icymushroom-df5abb57.japaneast.azurecontainerapps.io"

# シリアルポートの設定
port = "/dev/cu.M5StickAccel"  # 使用するポート名
baudrate = 115200  # ボーレートを115200に設定

id = str(uuid.uuid4())

last_send_time = 0

is_closing = False


def play_sound():
    pygame.mixer.music.load("watering.wav")
    pygame.mixer.music.play()


async def joro_main(websocket):
    global last_send_time
    global is_closing
    watering_array = []
    ser = serial.Serial(port, baudrate)
    try:
        while True:
            if ser.in_waiting > 0:
                data = float(ser.readline().decode("utf-8").rstrip())
                is_watering_now = data < -0.5
                if len(watering_array) > 5:
                    watering_array.pop(0)
                watering_array.append(is_watering_now)
                # 全てTrueなら水やり中
                is_watering = all(watering_array)
                print(data, is_watering)

                if last_send_time + 2 > time.time():
                    continue
                if is_watering == False:
                    continue

                # 水やりしている時
                threading.Thread(target=play_sound).start()  # 音声を別スレッドで再生
                last_send_time = time.time()
                message = json.dumps(
                    {
                        "head": {"type": "joro_status"},
                        "body": {"type": "joro", "uuid": id, "isWatering": is_watering},
                    }
                )
                await websocket.send(message)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
        is_closing = True
    finally:
        ser.close()
        print("Serial port closed.")


async def main():
    pygame.mixer.init()
    while True:
        if is_closing:
            break
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                # 接続後、特定のメッセージを送信
                initial_message = json.dumps(
                    {
                        "head": {"type": "init"},
                        "body": {"type": "joro", "uuid": id, "isWatering": False},
                    }
                )
                await websocket.send(initial_message)
                print(f"init done.")

                await joro_main(websocket)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.InvalidStatusCode,
            OSError,
        ) as e:
            print(f"WebSocket接続が切断されました: {e}. 再接続を試みます...")
            await asyncio.sleep(1)  # 1秒待機してから再接続を試みる


# 非同期タスクを実行
asyncio.run(main())
