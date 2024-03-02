from core_auto_app.application.interfaces import (
    ApplicationInterface,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command


class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application."""

    def __init__(self, camera: Camera, presenter: Presenter, robot_driver: RobotDriver):
        self._camera = camera
        self._presenter = presenter
        self._robot_driver = robot_driver

    def spin(self):
        self._camera.start()

        while True:
            # カメラ画像取得
            color, depth = self._camera.get_images()
            if color is None or depth is None:
                continue

            # ロボットの状態取得
            robot_state = self._robot_driver.get_robot_state()

            # 描画
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break
