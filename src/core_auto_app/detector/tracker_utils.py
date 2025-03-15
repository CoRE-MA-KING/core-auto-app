from motpy import Detection, MultiObjectTracker
import cv2
from core_auto_app.detector.object_class import CLASS_NAMES

def compute_iou(boxA, boxB):
    # boxA, boxB: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou

class ObjectTracker:
    def __init__(self, fps=18.99):
        """
        fps: カメラ映像のフレームレートを想定
             dt = 1/fps で時間刻みを設定している
        """
        self.tracker = MultiObjectTracker(
            dt=1/fps,
            model_spec={
                'order_pos': 1, 'dim_pos': 2,
                'order_size': 0, 'dim_size': 2,
                'q_var_pos': 5000., 'r_var_pos': 0.1
            }
        )
        self.track_id_counter = 1
        self.track_ids = {}
        # トラックごとに最新のクラスIDを保持する辞書
        self.track_cls = {}

    def update(self, detections):
        """
        detections: [(x1, y1, x2, y2, score, cls_id), ...]
          YOLOXDetector で取得した検出結果をそのまま入れられる形。
          motpyが必要とするDetection(box=[x1, y1, x2, y2], score=score)に変換。
        
        戻り値: [(x1, y1, x2, y2, track_id), ...]
          なお、トラックに紐付いたクラス情報は self.track_cls に記録される。
        """
        motpy_dets = []
        for (x1, y1, x2, y2, score, cls_id) in detections:
            d = Detection(box=[x1, y1, x2, y2], score=score)
            # 各Detectionにクラス情報を付加
            d.cls_id = cls_id
            motpy_dets.append(d)

        # motpyでステップ更新
        self.tracker.step(motpy_dets)
        tracks = self.tracker.active_tracks()

        results = []
        # 更新ごとにクラス情報のマッピングを再構築
        self.track_cls = {}
        for track in tracks:
            if track.id not in self.track_ids:
                self.track_ids[track.id] = self.track_id_counter
                self.track_id_counter += 1

            track_id = self.track_ids[track.id]
            box = list(map(int, track.box))
            results.append((box[0], box[1], box[2], box[3], track_id))

            # ヒューリスティックにより、各トラックに対して最も重なりのある検出からクラス情報を取得
            best_iou = 0.0
            best_cls = None
            for (x1, y1, x2, y2, score, cls_id) in detections:
                iou = compute_iou(box, [x1, y1, x2, y2])
                if iou > best_iou:
                    best_iou = iou
                    best_cls = cls_id
            # IoUが一定以上ならクラス情報として採用（閾値例：0.3）
            if best_iou > 0.3 and best_cls is not None:
                self.track_cls[track.id] = best_cls
            else:
                self.track_cls[track.id] = None

        return results

    def draw_boxes(self, frame, tracked_objects):
        """
        tracked_objects: [(x1, y1, x2, y2, track_id), ...]
        描画時に、トラックIDに加え、object_class.py のリソースからクラス名を表示する。
        """
        for (x1, y1, x2, y2, track_id) in tracked_objects:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # 逆引きして元のトラックID（motpy内部のID）を取得
            orig_track_id = None
            for k, v in self.track_ids.items():
                if v == track_id:
                    orig_track_id = k
                    break
            if orig_track_id is not None and orig_track_id in self.track_cls and self.track_cls[orig_track_id] is not None:
                cls_id = self.track_cls[orig_track_id]
                class_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "unknown"
            else:
                class_name = "unknown"
            txt = f"ID:{track_id} {class_name} center=({cx},{cy})"
            cv2.putText(frame, txt, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
