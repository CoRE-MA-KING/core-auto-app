import argparse
# import datetime
# import os
from typing import Optional

from core_auto_app.application.application import Application
from core_auto_app.infra.cv_presenter import CvPresenter
from core_auto_app.infra.realsense_camera import RealsenseCamera
from core_auto_app.infra.serial_robot_driver import SerialRobotDriver
from core_auto_app.infra.usb_camera import UsbCamera


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--robot_port",
        default="/dev/ttyACM0",
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
        default="/dev/front_camera",
        help="device file (symlink) of camera A (front camera)",
    )
    parser.add_argument(
        "--b_camera_name",
        default="/dev/back_camera",
        help="device file (symlink) of camera B (back camera)",
    )
    parser.add_argument(
        "--weight_path",
        default="/home/nvidia/core_auto_app/models/yolox_s/phase1_2_best_ckpt.pth",
        type=str,
        help="path to YOLOX weight file (.pth)"
    )
    args = parser.parse_args()
    return args


def run_application(
    robot_port: str, 
    record_dir: Optional[str], 
    a_camera_name, 
    b_camera_name,
    weight_path: str  # 追加
) -> None:
    """アプリケーションを実行する"""

    # 'record_dir'が存在しないパスだったときにエラーになるかも
    with RealsenseCamera(record_dir, weight_path) as realsense_camera, UsbCamera(
        a_camera_name
    ) as a_camera, UsbCamera(
        b_camera_name
    ) as b_camera, CvPresenter() as presenter, SerialRobotDriver(
        robot_port
    ) as robot_driver:
        app = Application(realsense_camera, a_camera, b_camera, presenter, robot_driver)
        app.spin()


def main():
    args = parse_args()
    run_application(
        record_dir=args.record_dir,
        robot_port=args.robot_port,
        a_camera_name=args.a_camera_name,
        b_camera_name=args.b_camera_name,
        weight_path=args.weight_path
    )


if __name__ == "__main__":
    main()
