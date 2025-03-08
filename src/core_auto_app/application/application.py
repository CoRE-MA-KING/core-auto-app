from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command
from core_auto_app.detector.object_detector import YOLOXDetector
from core_auto_app.detector.tracker_utils import ObjectTracker
from core_auto_app.detector.aiming.aiming_target_selector import AimingTargetSelector
import time

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
        # 照準対象を決定するクラス
        self._target_selector = AimingTargetSelector(image_center=(640, 360))

        # 照準対象を格納する変数
        self.aiming_target = None  # (cx, cy) を入れる想定

    def spin(self):
        # 各カメラ開始
        self._a_camera.start()
        self._b_camera.start()
        self._realsense_camera.start()

        # フレーム計測開始
        prev_time = time.time()
        frame_count = 0
        fps = 0.0  # 初期値を設定
        prev_frame_hash = None

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

                    # 3. バウンディングボックス描画（任意で残す）
                    self._tracker.draw_boxes(color, tracked_objects)

                    # 4. 照準対象の決定
                    self.aiming_target = self._target_selector.select_target(tracked_objects)

                    # 5. 現在の照準対象ID/座標を画面に表示（任意で残す）
                    self._target_selector.draw_aiming_target_info(color)

            else:
                # デフォルトでカメラA表示
                color = self._a_camera.get_image()

            # フレームが取得できなかった場合
            if color is None:
                color = self._a_camera.get_image()

            # フレーム計測
            frame_hash = hash(color.tobytes())  # フレームの簡易ハッシュを計算
            # 前回のフレームと異なる場合のみ、フレームカウントを増やす
            if frame_hash != prev_frame_hash:
                frame_count += 1
                prev_frame_hash = frame_hash

            now = time.time()
            elapsed = now - prev_time
            if elapsed >= 1.0:  # 1秒経過するごとにFPSを算出
                fps = frame_count / elapsed
                frame_count = 0
                prev_time = now
                # print(f"Current FPS: {fps:.2f}")  // コンソールに表示

            # FPS値を画面の左上(20,680)に表示 
            # cv2.putText(color, f"FPS {fps:.2f})", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            fps_disp = f"FPS {fps:.2f}"
            cv2.putText(color, fps_disp, (20, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 描画 (ここの指定によって画像の質が変わりそう)
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()
        self._a_camera.close()
        self._b_camera.close()
