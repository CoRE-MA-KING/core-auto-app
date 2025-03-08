import torch
import cv2
import numpy as np
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess

class YOLOXDetector:
    def __init__(self, model_path: str, score_thr: float = 0.99, nmsthre: float = 0.45):
        """
        model_path: 学習済みモデル(pthファイル)へのパス
        score_thr: 物体を検出する閾値
        nmsthre: NMS(重複を減らすための処理)のしきい値
        """
        self.exp = get_exp(None, "yolox-s")
        self.exp.num_classes = 1  # 今回は1クラスのみを想定
        self.model = self.exp.get_model()
        self.model.eval()

        # モデル重み読み込み
        ckpt = torch.load(model_path, map_location="cuda")
        self.model.load_state_dict(ckpt["model"])
        self.model.to("cuda")

        self.score_thr = score_thr
        self.nmsthre = nmsthre
        self.class_names = ["damage_panel"]  # クラス名

        # 検出対象の縦か横幅の検出閾値を設定
        self.size_x_thr = 100
        self.size_y_thr = 100

    def predict(self, frame: np.ndarray):
        """
        frame: カメラから取得したカラー画像 (BGR形式)
        戻り値: [(x1,y1,x2,y2,score,cls_id), ...] 形式の検出結果リスト
        """
        img, ratio = preproc(frame, (704, 1280))
        img = torch.from_numpy(img).unsqueeze(0)
        img = img.float().to("cuda")

        with torch.no_grad():
            outputs = self.model(img)
            outputs = postprocess(
                outputs, 
                self.exp.num_classes, 
                self.score_thr, 
                self.nmsthre, 
                class_agnostic=True
            )

        if outputs[0] is None:
            return []

        bboxes = outputs[0][:, 0:4].cpu() / ratio
        scores = (outputs[0][:, 4] * outputs[0][:, 5]).cpu()
        classes = outputs[0][:, 6].cpu().numpy().astype(int)

        results = []
        for bbox, score, cls_id in zip(bboxes, scores, classes):
            x1, y1, x2, y2 = bbox.numpy().astype(int)
            # 物体の幅または高さが50ピクセル未満なら除外
            if (x2 - x1) < self.size_x_thr or (y2 - y1) < self.size_y_thr:
                continue
            results.append((x1, y1, x2, y2, score.item(), cls_id))
        return results

    def draw_boxes(self, frame: np.ndarray, detections):
        """
        detections: predictメソッドで得た検出結果
        バウンディングボックスとスコア、クラス名を frame 上に描画
        """
        for (x1, y1, x2, y2, score, cls_id) in detections:
            class_name = self.class_names[cls_id]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, 
                        f"{class_name} {score:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.75, 
                        (0,255,0), 
                        2)
