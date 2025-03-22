import sys
import cv2

# カメラIDをコマンドライン引数から取得（指定がなければ0）
camera_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# 表示ウィンドウのサイズを指定（例：1920x1080）
window_width = 1280
window_height = 720
window_name = "CameraFeed"

# ウィンドウを通常モードで作成し、固定サイズに設定
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, window_width, window_height)

cap = cv2.VideoCapture(camera_id)
while True:
    ret, frame = cap.read()
    if not ret:
        print("Cannot retrieve frame")
        break

    # キャプチャしたフレームをウィンドウサイズにリサイズ
    frame_resized = cv2.resize(frame, (window_width, window_height))
    cv2.imshow(window_name, frame_resized)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
