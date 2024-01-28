from core_auto_app.application.application import Application

from core_auto_app.application.interfaces import Presenter
from core_auto_app.infra.realsense_camera import RealsenseCamera


class DummyPresenter(Presenter):
    def show(self, image):
        return

    def get_ui_command(self):
        pass

    def close(self):
        print("closing presenter")
        return


def main():
    camera = RealsenseCamera()
    presenter = DummyPresenter()

    app = Application(camera, presenter)

    try:
        app.spin()

    except KeyboardInterrupt as e:
        print(f"KeyboardInterrupt {e}")

    finally:
        app.close()


if __name__ == "__main__":
    main()
