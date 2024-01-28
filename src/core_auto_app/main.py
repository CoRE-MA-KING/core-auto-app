from core_auto_app.application.application import Application
from core_auto_app.infra.realsense_camera import RealsenseCamera
from core_auto_app.infra.cv_presenter import CvPresenter


def main():
    camera = RealsenseCamera()
    presenter = CvPresenter()

    app = Application(camera, presenter)

    try:
        app.spin()

    except KeyboardInterrupt as e:
        print(f"KeyboardInterrupt {e}")

    finally:
        app.close()


if __name__ == "__main__":
    main()
