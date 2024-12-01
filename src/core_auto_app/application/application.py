from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command

class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application."""

    def __init__(
        self,
        realsense_camera: Camera,
        a_camera: ColorCamera,
        b_camera: ColorCamera,
        presenter: Presenter,
        robot_driver: RobotDriver,
    ):
        self._realsense_camera = realsense_camera
        self._a_camera = a_camera
        self._b_camera = b_camera
        self._presenter = presenter
        self._robot_driver = robot_driver

        self._is_recording = False  # 録画状態のフラグ

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
