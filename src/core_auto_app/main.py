import argparse
import os
import re
from typing import Optional

from core_auto_app.application.application import Application
from core_auto_app.infra.cv_presenter import CvPresenter
from core_auto_app.infra.realsense_camera import RealsenseCamera
from core_auto_app.infra.serial_robot_driver import SerialRobotDriver
from core_auto_app.infra.usb_camera import UsbCamera

def get_video_number_from_symlink(symlink_path: str) -> int:
    """
    シンボリックリンクのターゲットから、数字（例："video6" の6）を抽出して返す関数
    """
    try:
        target = os.readlink(symlink_path)
        # 相対パスの場合は絶対パスに変換する
        if not os.path.isabs(target):
            target = os.path.join(os.path.dirname(symlink_path), target)
        match = re.search(r'(\d+)', target)
        if match:
            return int(match.group(1))
        else:
            raise ValueError(f"数字が見つかりません: {target}")
    except OSError as e:
        raise RuntimeError(f"シンボリックリンクの読み取りに失敗しました: {symlink_path}") from e

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
    a_camera_device: int, 
    b_camera_device: int,
    weight_path: str
) -> None:
    """アプリケーションを実行する"""
    with RealsenseCamera(record_dir, weight_path) as realsense_camera, \
         UsbCamera(a_camera_device) as a_camera, \
         UsbCamera(b_camera_device) as b_camera, \
         CvPresenter() as presenter, \
         SerialRobotDriver(robot_port) as robot_driver:
        app = Application(realsense_camera, a_camera, b_camera, presenter, robot_driver)
        app.spin()

def main():
    args = parse_args()
    # シンボリックリンクから実際のビデオ番号を取得する
    a_camera_device = get_video_number_from_symlink(args.a_camera_name)
    b_camera_device = get_video_number_from_symlink(args.b_camera_name)
    print("Front camera device number:", a_camera_device)
    print("Back camera device number:", b_camera_device)
    run_application(
        record_dir=args.record_dir,
        robot_port=args.robot_port,
        a_camera_device=a_camera_device,
        b_camera_device=b_camera_device,
        weight_path=args.weight_path
    )

if __name__ == "__main__":
    main()
