from typing import Union

import cv2
import numpy as np

from core_auto_app.application.interfaces import ColorCamera


class UsbCamera(ColorCamera):
    """Usbカメラからカラー画像を取得するクラス"""

    def __init__(self, filename: Union[int, str]):
        self._filename = filename
        self._capture = None

    @property
    def is_running(self):
        return self._capture is not None

    def start(self):
        """カメラストリームを開始させる"""
        self._capture = cv2.VideoCapture(self._filename)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def stop(self):
        """カメラストリームを停止させる"""
        self._capture.release()
        self._capture = None

    def get_image(self):
        """カラー画像を取得する

        Returns:
            color_image: カラー画像
        """
        assert self.is_running, "Camera not running. Please call start() first."

        # 新しいフレームを取得
        ret, frame = self._capture.read()

        # フレームが有効か確認
        if not ret:
            return None

        return frame

    def close(self):
        """カメラストリームを無効にする"""
        print("closing usb camera")
        if self.is_running:
            self.stop()
