from core_auto_app.application.interfaces import ApplicationInterface, Camera, Presenter
from core_auto_app.domain.messages import Command


class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application."""

    def __init__(self, camera: Camera, presenter: Presenter):
        self._camera = camera
        self._presenter = presenter

    def spin(self):
        self._camera.start()

        while True:
            color, depth = self._camera.get_images()
            if color is None or depth is None:
                continue

            self._presenter.show(color)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break
