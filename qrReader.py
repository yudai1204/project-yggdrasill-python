import cv2
import asyncio
import websockets
import json
import uuid
import time

# WebSocketサーバーのURL
SERVER_URL = "ws://localhost:3210"

# QRコード検出器を初期化
qr_detector = cv2.QRCodeDetector()

id = str(uuid.uuid4())


async def detect_qr_and_send(websocket):
    last_send_time = 0

    # カメラを初期化
    cap = cv2.VideoCapture(0)

    while True:
        try:
            # フレームをキャプチャ
            ret, frame = cap.read()
            if not ret:
                break

            # QRコードのデコードと位置の取得
            data, points, _ = qr_detector.detectAndDecode(frame)

            # 新しいQRコードが検出された場合にのみ表示と更新
            if data and points is not None:
                print(f"QRコードの値: {data}")

                # 4点の座標を描画
                points = points[0]
                for i in range(4):
                    next_index = (i + 1) % 4
                    pt1 = (int(points[i][0]), int(points[i][1]))
                    pt2 = (int(points[next_index][0]), int(points[next_index][1]))
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

                # QRコードの中心にテキストを表示
                cv2.putText(
                    frame,
                    data,
                    (int(points[0][0]), int(points[0][1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2,
                )

                # 前回から1秒以上経過していたら
                if last_send_time + 1 < time.time():
                    await send_qr_data(websocket, data, points)
                    last_send_time = time.time()

            # フレームを表示
            cv2.imshow("QRコード検出", frame)

            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.InvalidStatusCode,
        ) as e:
            print(f"WebSocket接続が切断されました: {e}. 再接続を試みます...")
            await asyncio.sleep(1)  # 1秒待機してから再接続を試みる
            break  # ループを抜けて再接続を試みる

    # リソース解放
    cap.release()
    cv2.destroyAllWindows()


# QRコードの値を送信
async def send_qr_data(websocket, qr_value, qr_points):
    qr_points_list = qr_points.tolist()
    # 1辺の長さの平均を計算
    qr_size = (
        sum(
            (
                (qr_points_list[i][0] - qr_points_list[(i + 1) % 4][0]) ** 2
                + (qr_points_list[i][1] - qr_points_list[(i + 1) % 4][1]) ** 2
            )
            ** 0.5
            for i in range(4)
        )
        / 4
    )

    message = json.dumps(
        {
            "head": {"type": "qrData"},
            "body": {
                "type": "qrReader",
                "uuid": id,
                "value": qr_value,
                "coordinates": qr_points_list,
                "size": qr_size,
            },
        }
    )
    await websocket.send(message)


async def main():
    while True:
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                # 接続後、特定のメッセージを送信
                initial_message = json.dumps(
                    {"head": {"type": "init"}, "body": {"type": "qrReader", "uuid": id}}
                )
                await websocket.send(initial_message)
                print(f"init done.")

                await detect_qr_and_send(websocket)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.InvalidStatusCode,
            OSError,
        ) as e:
            print(f"WebSocket接続が切断されました: {e}. 再接続を試みます...")
            await asyncio.sleep(1)  # 1秒待機してから再接続を試みる


# 非同期タスクを実行
asyncio.run(main())
