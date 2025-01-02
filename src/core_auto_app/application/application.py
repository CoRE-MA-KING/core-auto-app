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
    """Implementation for the CoRE auto-pilot application."""

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
        # weight_pathはmain.pyから受け取ったpthファイルのパス
        # ここでスコアしきい値(score_thr)やNMSしきい値(nmsthre)も調整可能
        self._detector = YOLOXDetector(weight_path, score_thr=0.8, nmsthre=0.45)

        # トラッキング初期化
        self._tracker = ObjectTracker(fps=30.0)

    def spin(self):
        self._a_camera.start()
        self._b_camera.start()
        self._realsense_camera.start()
        while True:
            # ロボットの状態取得
            robot_state = self._robot_driver.get_robot_state()
            # 録画設定の更新
            if robot_state.record_video and not self._is_recording:
                self._realsense_camera.start_recording()
                self._is_recording = True
            elif not robot_state.record_video and self._is_recording:
                self._realsense_camera.stop_recording()
                self._is_recording = False

            # カメラ画像取得
            if robot_state.video_id == 0:
                color = self._a_camera.get_image()
            elif robot_state.video_id == 1:
                color = self._b_camera.get_image()
            elif robot_state.video_id == 2:
                color, depth = self._realsense_camera.get_images()
                if color is not None:
                    # YOLOXで物体を検出
                    detections = self._detector.predict(color)
                    # detections: [(x1, y1, x2, y2, score, cls_id), ...]
                    
                    # 検出結果を描画（物体検出の結果）
                    # self._detector.draw_boxes(color, detections)

                    # トラッキング
                    tracked_objects = self._tracker.update(detections)
                    # tracked_objects: [(x1, y1, x2, y2, track_id), ...]

                    # 検出結果を描画（トラッキングの結果）
                    self._tracker.draw_boxes(color, tracked_objects)                    
                    
            else:
                color = self._a_camera.get_image()  # デフォルトでカメラAの画像

            if color is None:
                color = self._a_camera.get_image()  # 取得できなかった場合はカメラAの画像

            # 描画 (ここの指定によって画像の質が変わりそう)
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()
        self._a_camera.close()
        self._b_camera.close()
