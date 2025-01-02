from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command
from core_auto_app.detector.object_detector import YOLOXDetector  # YOLOXの物体検出用クラス
from core_auto_app.detector.tracker_utils import ObjectTracker  # トラッキング用クラス
import cv2

class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application.
       トラッキング対象物体の中心ピクセル座標を画面に表示するだけ。
       奥行き情報(深度)・3次元変換は不要。
    """

    def __init__(
        self,
        realsense_camera: Camera,
        a_camera: ColorCamera,
        b_camera: ColorCamera,
        presenter: Presenter,
        robot_driver: RobotDriver,
        weight_path: str  # コマンドライン引数で渡すモデルファイルパス
    ):
        self._realsense_camera = realsense_camera
        self._a_camera = a_camera
        self._b_camera = b_camera
        self._presenter = presenter
        self._robot_driver = robot_driver

        self._is_recording = False

        # YOLOXの物体検出初期化
        self._detector = YOLOXDetector(weight_path, score_thr=0.8, nmsthre=0.45)

        # トラッキング初期化
        self._tracker = ObjectTracker(fps=30.0)

    def spin(self):
        # 各カメラ開始
        self._a_camera.start()
        self._b_camera.start()
        self._realsense_camera.start()

        while True:
            # ロボットの状態取得
            robot_state = self._robot_driver.get_robot_state()

            # 録画設定の更新（record_videoフラグでstart/stop）
            if robot_state.record_video and not self._is_recording:
                self._realsense_camera.start_recording()
                self._is_recording = True
            elif not robot_state.record_video and self._is_recording:
                self._realsense_camera.stop_recording()
                self._is_recording = False

            # カメラ画像取得 (video_idで切り替え)
            if robot_state.video_id == 0:
                color = self._a_camera.get_image()
            elif robot_state.video_id == 1:
                color = self._b_camera.get_image()
            elif robot_state.video_id == 2:
                color, depth = self._realsense_camera.get_images()
                # ここで物体検出＆トラッキング実施
                if color is not None:
                    # 1. 物体検出
                    detections = self._detector.predict(color)
                    # detections: [(x1, y1, x2, y2, score, cls_id), ...]

                    # 2. トラッキング
                    tracked_objects = self._tracker.update(detections)
                    # tracked_objects: [(x1, y1, x2, y2, track_id), ...]

                    # 3. 物体の中心座標を表示（ID付き）
                    self._draw_center_positions(color, tracked_objects)

                    # 4. バウンディングボックス描画（任意で残す）
                    self._tracker.draw_boxes(color, tracked_objects)
            else:
                # デフォルトでカメラA表示
                color = self._a_camera.get_image()

            # フレームが取得できなかった場合
            if color is None:
                color = self._a_camera.get_image()

            # 描画 (ここの指定によって画像の質が変わりそう)
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()
        self._a_camera.close()
        self._b_camera.close()

    def _draw_center_positions(self, frame, tracked_objects):
        """
        トラッキングされた物体の中心ピクセル座標(cx, cy)を画面に描画する。
        Args:
            frame: BGRカラー画像
            tracked_objects: [(x1, y1, x2, y2, track_id), ...]
        """
        for (x1, y1, x2, y2, t_id) in tracked_objects:
            # 中心座標
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # テキスト表示 (IDと中心座標)
            txt = f"ID:{t_id} center=({cx},{cy})"
            cv2.putText(frame, txt, (x1, max(y1 - 10, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,255,0), 2)

            # 中心点にマークをつける例 (小さな円)
            cv2.circle(frame, (cx, cy), 3, (0,255,255), -1)
