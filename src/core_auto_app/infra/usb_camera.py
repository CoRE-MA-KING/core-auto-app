from typing import Union
import threading

import cv2
import numpy as np

from core_auto_app.application.interfaces import ColorCamera


class UsbCamera(ColorCamera):
    """USBカメラからカラー画像を取得するクラス（スレッド対応版）"""

    def __init__(self, filename: Union[int, str]):
        self._filename = filename
        self._capture = None
        self._is_running = False
        self._frame_lock = threading.Lock()
        self._frame = None
        self._thread = None

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        """カメラストリームを開始させる"""
        if not self._is_running:
            self._capture = cv2.VideoCapture(self._filename)
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self._is_running = True
            # フレーム取得スレッドの開始
            self._thread = threading.Thread(target=self._update_frames, daemon=True)
            self._thread.start()
            print(f"USB camera {self._filename} started.")
        else:
            print(f"USB camera {self._filename} is already running.")

    def stop(self):
        """カメラストリームを停止させる"""
        if self._is_running:
            self._is_running = False
            if self._thread is not None:
                self._thread.join()
            if self._capture is not None:
                self._capture.release()
                self._capture = None
            self._thread = None
            print(f"USB camera {self._filename} stopped.")
        else:
            print(f"USB camera {self._filename} is not running.")

    def _update_frames(self):
        """フレームを継続的に取得するスレッド用メソッド"""
        while self._is_running:
            ret, frame = self._capture.read()
            if not ret:
                continue
            with self._frame_lock:
                self._frame = frame

    def get_image(self):
        """最新のカラー画像を取得する

        Returns:
            color_image: カラー画像（numpy.ndarray）
        """
        with self._frame_lock:
            frame = self._frame.copy() if self._frame is not None else None
        return frame

    def close(self):
        """カメラストリームを無効にする"""
        print(f"Closing USB camera {self._filename}")
        self.stop()
