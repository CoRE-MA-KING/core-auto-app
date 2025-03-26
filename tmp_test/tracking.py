import cv2
from screeninfo import get_monitors
import numpy as np
import torch
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess, vis

# YOLOXカスタムクラス（5クラスに変更）
CUSTOM_CLASSES = [
    "damage_panel",
    "damage_panel2",
    "damage_panel3",
    "damage_panel4",
    "damage_panel5"
]

# 表示画像
FULLSCREEN_W = 1220
FULLSCREEN_H = 720

# 撮影画像
CAPTURE_IMAGE_W = 1280
CAPTURE_IMAGE_H = 720

# 推論画像
PREDICT_IMAGE_W = 1280
PREDICT_IMAGE_H = 704

SCALE_WIDTH = FULLSCREEN_W / CAPTURE_IMAGE_W
SCALE_HEIGHT = FULLSCREEN_H / CAPTURE_IMAGE_H
SCALE = min(SCALE_WIDTH, SCALE_HEIGHT)
FULLSCREEN_IMAGE_WIDTH = int(CAPTURE_IMAGE_W * SCALE)
FULLSCREEN_IMAGE_HEIGHT = int(CAPTURE_IMAGE_H * SCALE)
IMAGE_INIT_X = (FULLSCREEN_W - FULLSCREEN_IMAGE_WIDTH) // 2
IMAGE_INIT_Y = (FULLSCREEN_H - FULLSCREEN_IMAGE_HEIGHT) // 2

cv2.namedWindow("yolox_detection", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("yolox_detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# デバッグ用：生のフレーム表示ウィンドウ
cv2.namedWindow("raw", cv2.WINDOW_NORMAL)

# キャンバスを準備
canvas = np.zeros((FULLSCREEN_H, FULLSCREEN_W, 3), dtype="uint8")

# 表示するモニターを確保
monitor = get_monitors()[0]

# YOLOXのモデル設定とロード
exp = get_exp(None, "yolox-s")
exp.num_classes = 5  # 5クラスに変更
model = exp.get_model()
model.eval()

# 重みのロード（5クラス用のチェックポイントを指定）
ckpt = torch.load("../models/yolox_s/phase1_2_best_ckpt.pth", map_location="cuda")
model.load_state_dict(ckpt["model"])

# モデル全体をGPUにロード
model.to("cuda")

# カメラデバイスを"/dev/video4"に指定（必要に応じて正しいデバイス番号に変更してください）
cap = cv2.VideoCapture("/dev/video4")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_IMAGE_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_IMAGE_H)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームを取得できません")
            break

        # デバッグ用：生のフレーム表示
        cv2.imshow("raw", frame)

        # 前処理（リサイズなど）
        img, ratio = preproc(frame, (PREDICT_IMAGE_H, PREDICT_IMAGE_W))
        img = torch.from_numpy(img).unsqueeze(0).float().to("cuda")

        # 推論
        with torch.no_grad():
            outputs = model(img)
            outputs = postprocess(outputs, exp.num_classes, 0.8, exp.nmsthre, class_agnostic=True)

        # 推論結果を描画
        if outputs[0] is not None:
            bboxes = outputs[0][:, 0:4] / ratio
            cls = outputs[0][:, 6]
            scores = outputs[0][:, 4] * outputs[0][:, 5]
            vis_res = vis(frame, bboxes, scores, cls, 0.8, CUSTOM_CLASSES)
        else:
            vis_res = frame

        # フルスクリーン表示用にリサイズしてキャンバスに描画
        img_resized = cv2.resize(
            vis_res,
            (FULLSCREEN_IMAGE_WIDTH, FULLSCREEN_IMAGE_HEIGHT),
            interpolation=cv2.INTER_AREA
        )
        canvas[IMAGE_INIT_Y:IMAGE_INIT_Y+FULLSCREEN_IMAGE_HEIGHT,
               IMAGE_INIT_X:IMAGE_INIT_X+FULLSCREEN_IMAGE_WIDTH] = img_resized
        cv2.imshow("yolox_detection", canvas)

        # キー待ち（"q"でループ終了）
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
except KeyboardInterrupt:
    print("KeyboardInterruptが検出されました。終了します。")
finally:
    cap.release()
    cv2.destroyAllWindows()
