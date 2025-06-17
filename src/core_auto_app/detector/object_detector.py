import torch
import cv2
import numpy as np
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess
from core_auto_app.detector.object_class import CLASS_NAMES  # 追加

class YOLOXDetector:
    def __init__(self, model_path: str, score_thr: float = 0.8, nmsthre: float = 0.45):
        """
        model_path: 学習済みモデル(pthファイル)へのパス
        score_thr: 物体を検出する閾値（デフォルト0.8）
        nmsthre: NMS(重複を減らすための処理)のしきい値
        """
        self.exp = get_exp(None, "yolox-s")
        self.exp.num_classes = len(CLASS_NAMES)  # クラス数をリソースに合わせる
        self.model = self.exp.get_model()
        self.model.eval()

        # モデル重み読み込み
        ckpt = torch.load(model_path, map_location="cuda")
        self.model.load_state_dict(ckpt["model"])
        self.model.to("cuda")

        self.score_thr = score_thr
        self.nmsthre = nmsthre
        # クラス名はリソースファイルから取得
        self.class_names = CLASS_NAMES

        # 検出対象のサイズ閾値
        self.size_x_thr = 15
        self.size_y_thr = 50

    def predict(self, frame: np.ndarray):
        """
        frame: カメラから取得したカラー画像 (BGR形式)
        戻り値: [(x1, y1, x2, y2, score, cls_id), ...] 形式の検出結果リスト
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
            # 物体の幅または高さが閾値未満なら除外
            if (x2 - x1) < self.size_x_thr or (y2 - y1) < self.size_y_thr:
                continue
            results.append((x1, y1, x2, y2, score.item(), cls_id))

        # スコアが0.8以上の検出結果のみを対象とし、最もスコアが高いものを採用
        valid_results = [det for det in results if det[4] >= self.score_thr]
        if valid_results:
            best_detection = max(valid_results, key=lambda det: det[4])
            return [best_detection]
        return []

    def draw_boxes(self, frame: np.ndarray, detections):
        """
        detections: predictメソッドで得た検出結果
        バウンディングボックスとスコア、クラス名を frame 上に描画
        """
        for (x1, y1, x2, y2, score, cls_id) in detections:
            # リソースファイルからクラス名を取得
            class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else "unknown"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # cv2.putText(frame, 
            #             f"{class_name} {score:.2f}",
            #             (x1, y1 - 10),
            #             cv2.FONT_HERSHEY_SIMPLEX, 
            #             0.75, 
            #             (0, 255, 0), 
            #             2)
