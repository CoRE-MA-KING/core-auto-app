from core_auto_app.application.application import Application

from core_auto_app.application.interfaces import Camera, Presenter


class DummyCamera(Camera):
    def start(self):
        return

    def stop(self):
        return

    def get_images(self):
        return None, None

    def close(self):
        print("closing camera")
        return


class DummyPresenter(Presenter):
    def show(self, image):
        return

    def get_ui_command(self):
        pass

    def close(self):
        print("closing presenter")
        return


def main():
    camera = DummyCamera()
    presenter = DummyPresenter()

    app = Application(camera, presenter)

    try:
        app.spin()

    except Exception as e:
        print(e)

    finally:
        app.close()


if __name__ == "__main__":
    main()
