import websockets
import uuid
import json
import asyncio

# WebSocketサーバーのURL
SERVER_URL = "ws://localhost:3210"

id = str(uuid.uuid4())


async def joro_main(websocket):
    for i in range(3):
        await asyncio.sleep(1)
        # 1秒ごとにjキーが押されているか確認
        # jが押されていたら、isWateringをTrueにして送信
        print("sent!")
        message = json.dumps(
            {
                "head": {"type": "joro_status"},
                "body": {"type": "joro", "uuid": id, "isWatering": True},
            }
        )
        await websocket.send(message)


async def main():
    # while True:
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
