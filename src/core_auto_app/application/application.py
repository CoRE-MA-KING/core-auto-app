from core_auto_app.application.interfaces import (
    ApplicationInterface,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command
from core_auto_app.detector.object_detector import YOLOXDetector
# from core_auto_app.detector.tracker_utils import ObjectTracker
# from core_auto_app.detector.aiming.aiming_target_selector import AimingTargetSelector
import time
import cv2

class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application.
       トラッキングを使わず、YOLOXの認識結果から最も中央に近い物体を照準対象にする。
    """

    def __init__(
        self,
        realsense_camera: Camera,
        presenter: Presenter,
        robot_driver: RobotDriver,
        weight_path: str  # コマンドライン引数で渡すモデルファイルパス
    ):
        self._realsense_camera = realsense_camera
        self._presenter = presenter
        self._robot_driver = robot_driver
        self._is_recording = False

        # YOLOXの物体検出初期化
        self._detector = YOLOXDetector(weight_path, score_thr=0.8, nmsthre=0.45)

        # --- トラッキングを廃止するので以下は不要 ---
        # self._tracker = ObjectTracker(fps=30.0)
        # self._target_selector = AimingTargetSelector(image_center=(640, 360))

        # 照準対象を格納する変数
        self.aiming_target = None  # (cx, cy) を入れる想定

    def spin(self):
        # カメラ開始
        self._realsense_camera.start()

        prev_time = time.time()
        frame_count = 0

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

            # カメラ画像取得
            color, depth = self._realsense_camera.get_images()

            if color is not None:
                # 1. 物体検出 (YOLOX)
                detections = self._detector.predict(color)
                # detections: [(x1, y1, x2, y2, score, cls_id), ...]

                # （任意）検出結果の描画
                self._detector.draw_boxes(color, detections)

                # 2. 最も中央画素(640,360)に近い物体を選ぶ
                self.aiming_target = self._select_closest_to_center(detections, center=(640,360))

            # フレーム計測
            frame_count += 1
            now = time.time()
            elapsed = now - prev_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                print(f"Current FPS: {fps:.2f}")
                frame_count = 0
                prev_time = now

            # 送信データ作成
            target_depth = 0
            target_tmp = 0
            (target_x, target_y) = (640, 360)
            if self.aiming_target is not None:
                (target_x, target_y) = self.aiming_target

            send_str = f"{target_x},{target_y},{target_depth},{target_tmp}\n"
            # 別スレッドで送信
            self._robot_driver.set_send_data(send_str)

            # 描画
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()
            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()

    def _select_closest_to_center(self, detections, center=(640, 360)):
        """
        YOLOXの検出結果(detections)の中から、
        中央(center)に最も近い物体を1つ選び、その中心(cx,cy)を返す。
        何もなければNoneを返す。
        """
        if not detections:
            return None

        center_x, center_y = center
        min_dist = None
        chosen_xy = None

        for (x1, y1, x2, y2, score, cls_id) in detections:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            dx = cx - center_x
            dy = cy - center_y
            dist_sq = dx*dx + dy*dy  # ユークリッド距離の2乗(距離計算に sqrt不要なら2乗でOK)
            if min_dist is None or dist_sq < min_dist:
                min_dist = dist_sq
                chosen_xy = (cx, cy)

        return chosen_xy
