import argparse
import datetime
import os
from typing import Optional

from core_auto_app.application.application import Application
from core_auto_app.infra.realsense_camera import RealsenseCamera
from core_auto_app.infra.cv_presenter import CvPresenter


def main(record_dir: Optional[str]):
    # 引数と日時から録画の保存先のファイルパスを決定
    if record_dir:
        dt_now = datetime.datetime.now()
        record_path = os.path.join(
            record_dir, dt_now.strftime("camera_%Y%m%d_%H%M%S.bag")
        )
        print(f"Camera record path: {record_path}")
    else:
        record_path = None
        print("Directory not specified. Disable camera recording.")

    camera = RealsenseCamera(record_path=record_path)
    presenter = CvPresenter()

    app = Application(camera, presenter)

    try:
        app.spin()

    except KeyboardInterrupt as e:
        print(f"KeyboardInterrupt {e}")

    finally:
        app.close()


if __name__ == "__main__":
    # コマンドライン引数
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record_dir",
        default=None,
        type=str,
        help="directory to record camera log",
    )
    args = parser.parse_args()

    main(record_dir=args.record_dir)
