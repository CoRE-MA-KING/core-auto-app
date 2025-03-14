from motpy import Detection, MultiObjectTracker
import cv2

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

    def update(self, detections):
        """
        detections: [(x1, y1, x2, y2, score, cls_id), ...]
          YOLOXDetector で取得した検出結果をそのまま入れられる形。
          motpyが必要とするDetection(box=[x1, y1, x2, y2], score=score)に変換。

        戻り値: [(x1, y1, x2, y2, track_id), ...]
          motpyが更新した結果としてのトラック情報。
          track_idは独自に付け替えている（motpy内部のidは文字列/ハッシュ値のため）。
        """
        motpy_dets = []
        for (x1, y1, x2, y2, score, cls_id) in detections:
            # Detectionのboxは [x1, y1, x2, y2]
            # scoreも設定できる
            motpy_dets.append(Detection(box=[x1, y1, x2, y2], score=score))

        # motpyでステップ更新
        self.tracker.step(motpy_dets)
        tracks = self.tracker.active_tracks()

        # 結果を[(x1, y1, x2, y2, track_id), ...]に変換
        results = []
        for track in tracks:
            # motpy独自のtrack.idをこちらで数字IDに変換
            if track.id not in self.track_ids:
                self.track_ids[track.id] = self.track_id_counter
                self.track_id_counter += 1

            track_id = self.track_ids[track.id]
            x1, y1, x2, y2 = map(int, track.box)
            results.append((x1, y1, x2, y2, track_id))

        return results

    def draw_boxes(self, frame, tracked_objects):
        """
        tracked_objects: [(x1, y1, x2, y2, track_id), ...]
        track_idは連番ID
        """
        for (x1, y1, x2, y2, track_id) in tracked_objects:
            # 今回はクラス名を固定（例: "damage_panel"）
            # クラス名を複数管理するなら別途ロジックを追加

            # 中心座標
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            txt = f"ID:{track_id}  center=({cx},{cy})"
            cv2.putText(frame, txt, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,255,0), 2)
            # 中心点にマークをつける例 (小さな円)
            cv2.circle(frame, (cx, cy), 3, (0,255,255), -1)
