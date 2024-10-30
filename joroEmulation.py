import websockets
import uuid
import json
import asyncio

# WebSocketサーバーのURL
SERVER_URL = "ws://localhost:3210"
# SERVER_URL = "wss://project-yggdrasill-backend.icymushroom-df5abb57.japaneast.azurecontainerapps.io"

id = str(uuid.uuid4())


async def joro_main(websocket):
    for i in range(3):
        await asyncio.sleep(1)
        message = json.dumps(
            {
                "head": {"type": "joro_status"},
                "body": {"type": "joro", "uuid": id, "isWatering": True},
            }
        )
        await websocket.send(message)
        print("sent!")


async def main():
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


# 非同期タスクを実行
asyncio.run(main())
