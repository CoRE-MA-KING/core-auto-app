from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command
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
        # 重い検出処理はrealsense_camera側で行うので、ここでは重みの初期化は不要
    ):
        self._realsense_camera = realsense_camera
        self._a_camera = a_camera
        self._b_camera = b_camera
        self._presenter = presenter
        self._robot_driver = robot_driver

        self._is_recording = False

        # Application側では、Realsenseで計算された検出結果を参照する
        self.aiming_target = (0, 0)  # (cx, cy) を入れる想定

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
                # Realsense側で常時検出している結果を取得して描画する
                detection_results = self._realsense_camera.get_detection_results()
                if detection_results is not None:
                    self._realsense_camera.draw_detection_results(color, detection_results)
            else:
                # デフォルトでカメラA表示
                color = self._a_camera.get_image()

            # Realsenseによる最新の照準対象を取得
            self.aiming_target = self._realsense_camera.get_aiming_target()
            if self.aiming_target is None:
                self.aiming_target = (640, 360)  # 照準対象がいない場合は(0, 0)を送信

            self.draw_aiming_target_info(color, self.aiming_target)
            # マイコンに送信する値を更新（形式: "%d,%d,%d\n"）
            self._robot_driver.set_send_values(self.aiming_target[0], self.aiming_target[1], 0)

            # フレーム計測
            if color is not None:
                frame_hash = hash(color.tobytes())  # フレームの簡易ハッシュを計算
                if frame_hash != prev_frame_hash:
                    frame_count += 1
                    prev_frame_hash = frame_hash

            now = time.time()
            elapsed = now - prev_time
            if elapsed >= 1.0 and elapsed != 0:  # 1秒経過するごとにFPSを算出
                fps = frame_count / elapsed
                frame_count = 0
                prev_time = now
                # print(f"Current FPS: {fps:.2f}")

            # FPS値を画面の左上(20,680)に表示 
            fps_disp = f"FPS {fps:.2f}"
            cv2.putText(color, fps_disp, (20, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 描画
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()
        self._a_camera.close()
        self._b_camera.close()

    def draw_aiming_target_info(self, frame, aiming_target):
        """
        現在の照準対象IDと座標を画面左上に描画
        """
        (cx, cy) = aiming_target
        txt = f"Target: ({cx},{cy})"
        # 左上(20,50)に表示 (お好みで位置を調整)
        cv2.putText(frame, txt, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
