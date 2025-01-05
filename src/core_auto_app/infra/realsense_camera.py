import datetime
import os
import threading

from typing import Optional

import numpy as np
import pyrealsense2 as rs

from core_auto_app.application.interfaces import Camera


class RealsenseCamera(Camera):
    """RealSenseカメラからカラー画像とデプス画像を取得するクラス

    Args:
        record_path: 録画の保存先のファイルパス

    Attributes:
        pipeline: RealSenseのパイプライン
        config: RealSenseの設定

    Notes:
        https://intelrealsense.github.io/librealsense/python_docs/_generated/pyrealsense2.html
    """

    def __init__(self, record_dir: Optional[str] = None):
        # パイプラインと設定の初期化（開始はしない）
        self._pipeline = rs.pipeline()
        self._config = rs.config()
        # ストリームの設定
        self._config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        self._config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

        # カラーフレームとデプスフレームを整列させるalignオブジェクト
        self._align = rs.align(align_to=rs.stream.color)

        self._record_dir = record_dir
        self._is_running = False
        self.recorder = None  # Recorderオブジェクトを初期化

        # フレーム取得用の変数
        self._frame_lock = threading.Lock()
        self._color_frame = None
        self._depth_frame = None
        self._thread = None

        # パイプライン情報取得のための変数
        self._pipeline_profile = None

        print("init realsense camera")

    @property
    def pipeline_profile(self):
        """RealSenseのパイプラインプロファイルを返すプロパティ"""
        return self._pipeline_profile

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        """カメラストリームを開始させる"""
        if not self._is_running:
            try:
                print("start realsense stream")
                self._pipeline_profile = self._pipeline.start(self._config)
                self._is_running = True
                # フレーム取得のためにスレッドを開始
                self._thread = threading.Thread(target=self.update_farames, daemon=True)
                self._thread.start()
            except RuntimeError as err:
                print(err)
                self._is_running = False
        else:
            print("Realsense camera is already running")

    def stop(self):
        """カメラストリームを停止させる"""
        if self._is_running:
            print("stop realsense stream")
            self._is_running = False
            if self._thread is not None:
                self._thread.join()
            self._pipeline.stop()
            self._config.disable_all_streams()
            self.recorder = None  # Recorderオブジェクトをリセット
        else:
            print("Realsense camera is not running.")

    def update_farames(self):
        """カメラからフレームを取得し続けるスレッド用メソッド"""
        while self._is_running:
            frames = self._pipeline.wait_for_frames()
            # デプスとカラーを整列させたフレームを取得する
            aligned_frames = self._align.process(frames)
            # カラーとデプスそれぞれ取り出す
            color_frame = aligned_frames.get_color_frame()
            aligned_depth_frame = aligned_frames.get_depth_frame()
            # フレームが有効か確認
            if not aligned_depth_frame or not color_frame:
                continue
            # フレームをNumpy配列に変換
            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            # フレームを保存
            with self._frame_lock:
                self._color_frame = color_image
                self._depth_frame = depth_image

    def get_images(self):
        """カラー画像とデプス画像を取得する

        Returns:
            color_image: カラー画像
            depth_image: デプス画像
        """
        with self._frame_lock:
            color_image = self._color_frame
            depth_image = self._depth_frame
        return color_image, depth_image

    def start_recording(self):
        """録画を開始する

        Args:
            record_path: 録画の保存先のファイルパス
        """
        if self.recorder is None:
            if self._record_dir is None:
                print("Record directory is not specified.")
                return
            dt_now = datetime.datetime.now()
            record_path = os.path.join(
                self._record_dir, dt_now.strftime("camera_%Y%m%d_%H%M%S.bag")
            )
            print(f"Start recording to {record_path}")
            device = self.pipeline_profile.get_device()
            self.recorder = rs.recorder(record_path, device)
        else:
            print("Recording is already in progress.")

    def stop_recording(self):
        """録画を停止する"""
        if self.recorder is not None:
            print("Stop recording")
            self.recorder.pause()
            self.recorder = None
        else:
            print("Recording is not in progress.")

    def close(self):
        """カメラストリームを無効にする"""
        print("closing realsense camera")
        self.stop()
