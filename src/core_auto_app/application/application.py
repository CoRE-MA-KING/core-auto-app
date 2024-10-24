from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    CameraFactory,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command

class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application."""

    def __init__(
        self,
        camera_factory: CameraFactory,
        a_camera: ColorCamera,
        b_camera: ColorCamera,
        presenter: Presenter,
        robot_driver: RobotDriver,
    ):
        self._camera_factory = camera_factory
        self._a_camera = a_camera
        self._b_camera = b_camera
        self._presenter = presenter
        self._robot_driver = robot_driver

        self._prev_record = False
        self._camera = self._camera_factory.create(record_flag=False)

    def spin(self):
        self._a_camera.start()
        self._b_camera.start()
        while True:
            # ロボットの状態取得
            robot_state = self._robot_driver.get_robot_state()
            # 録画設定の更新
            if robot_state.record_video != self._prev_record:
                self._camera = self._camera_factory.create(robot_state.record_video)
                self._prev_record = robot_state.record_video
                # NOTE: フルスクリーンがバグったときのためウィンドウを作り直す
                self._presenter.recreate_window()

            # カメラ画像取得
            if robot_state.video_id == 0:
                color = self._a_camera.get_image()
            elif robot_state.video_id == 1:
                color = self._b_camera.get_image()
            elif robot_state.video_id == 2:
                color, depth = self._camera.get_images()

            # 指定されたカメラ画像を取得できなかった場合、カメラAの画像を再取得
            if color is None:
                color = self._a_camera.get_image()

            # 描画 (ここの指定によって画像の質が変わりそう)
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break
