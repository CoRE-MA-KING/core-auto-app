from typing import Optional

import numpy as np
import pyrealsense2 as rs

from core_auto_app.application.interfaces import Camera, CameraFactory


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

    def __init__(self, record_path: Optional[str] = None):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

        # カラーフレームとデプスフレームを整列させるalignオブジェクト
        self.align = rs.align(align_to=rs.stream.color)

        # 保存先が指定されていた場合、録画機能を有効にする
        if record_path:
            self.config.enable_record_to_file(record_path)

        self._is_running = False

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        """カメラストリームを開始させる"""
        self.pipeline.start(self.config)
        self._is_running = True

    def stop(self):
        """カメラストリームを停止させる"""
        self.pipeline.stop()
        self._is_running = False

    def get_images(self):
        """カラー画像とデプス画像を取得する

        Returns:
            color_image: カラー画像
            depth_image: デプス画像
        """
        assert self.is_running, "Camera not running. Please call start() first."

        # 新しいフレームを取得
        frames = self.pipeline.wait_for_frames()

        # デプスとカラーを整列させたフレームを取得する
        aligned_frames = self.align.process(frames)

        # カラーとデプスそれぞれ取り出す
        color_frame = aligned_frames.get_color_frame()
        aligned_depth_frame = aligned_frames.get_depth_frame()

        # フレームが有効か確認
        if not aligned_depth_frame or not color_frame:
            return None, None

        # フレームをNumpy配列に変換
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        return color_image, depth_image

    def close(self):
        """カメラストリームを無効にする"""
        print("closing camera")
        if self.is_running:
            self.stop()
        self.config.disable_all_streams()


class RealsenseCameraFactory(CameraFactory):
    """RealSenseカメラの作成と破棄を担うクラス

    Args:
        record_path: 録画の保存先のファイルパス
    """

    def __init__(self, record_path: str):
        self._record_path: str = record_path
        self._camera: Camera = RealsenseCamera(None)

    def create(self, record: bool) -> Camera:
        print("creating camera")
        tmp_record_path = self._record_path if record else None
        self._camera.close()
        self._camera = RealsenseCamera(tmp_record_path)
        return self._camera

    def close(self):
        print("closing camera factory")
        self._camera.close()
