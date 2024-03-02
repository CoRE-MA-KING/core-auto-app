import argparse
import datetime
import os
from typing import Optional

from core_auto_app.application.application import Application
from core_auto_app.infra.realsense_camera import RealsenseCamera
from core_auto_app.infra.cv_presenter import CvPresenter
from core_auto_app.infra.serial_robot_driver import SerialRobotDriver


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--robot_port",
        default="/dev/ttyUSB0",
        type=str,
        help="serial port for communicating with robot",
    )
    parser.add_argument(
        "--record_dir",
        default=None,
        type=str,
        help="directory to record camera log",
    )
    args = parser.parse_args()
    return args


def run_application(robot_port: str, record_dir: Optional[str]) -> None:
    """アプリケーションを実行する"""
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

    with RealsenseCamera(
        record_path
    ) as camera, CvPresenter() as presenter, SerialRobotDriver(
        robot_port, baudrate=9600
    ) as robot_driver:
        app = Application(camera, presenter, robot_driver)
        app.spin()


def main():
    args = parse_args()
    run_application(record_dir=args.record_dir, robot_port=args.robot_port)


if __name__ == "__main__":
    main()
