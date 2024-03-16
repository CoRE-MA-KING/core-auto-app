import argparse
import datetime
import os
from typing import Optional

from core_auto_app.application.application import Application
from core_auto_app.infra.cv_presenter import CvPresenter
from core_auto_app.infra.realsense_camera import RealsenseCameraFactory
from core_auto_app.infra.serial_robot_driver import SerialRobotDriver
from core_auto_app.infra.usb_camera import UsbCamera


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
        default="/mnt/ssd1",
        type=str,
        help="directory to record camera log",
    )
    parser.add_argument(
        "--a_camera_name",
        default=6,
        help="number or filename of camera A",
    )
    args = parser.parse_args()
    return args


def run_application(robot_port: str, record_dir: Optional[str], a_camera_name) -> None:
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

    with RealsenseCameraFactory(record_path) as camera_factory, UsbCamera(
        a_camera_name
    ) as a_camera, CvPresenter() as presenter, SerialRobotDriver(
        robot_port
    ) as robot_driver:
        app = Application(camera_factory, a_camera, presenter, robot_driver)
        app.spin()


def main():
    args = parse_args()
    run_application(
        record_dir=args.record_dir,
        robot_port=args.robot_port,
        a_camera_name=args.a_camera_name,
    )


if __name__ == "__main__":
    main()
