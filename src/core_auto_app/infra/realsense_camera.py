import datetime
import os
import threading
import time

from typing import Optional

import numpy as np
import pyrealsense2 as rs

from core_auto_app.application.interfaces import Camera

# 検出用モジュールのインポート
from core_auto_app.detector.object_detector import YOLOXDetector
from core_auto_app.detector.tracker_utils import ObjectTracker
from core_auto_app.detector.aiming.aiming_target_selector import AimingTargetSelector

class RealsenseCamera(Camera):
    """RealSenseカメラからカラー画像とデプス画像を取得するクラス
       さらに、内部でYOLOXによる物体検出とトラッキングを非同期で実行し、
       最新の検出結果を取得できるようにする
    """

    def __init__(self, record_dir: Optional[str] = None, weight_path: Optional[str] = None):
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
        self._frame_thread = None

        # 検出結果と関連する変数用のロック
        self._detection_lock = threading.Lock()
        self._detection_result = None
        self._aiming_target = None

        # 検出用スレッド
        self._detection_thread = None

        # パイプライン情報取得のための変数
        self._pipeline_profile = None

        # YOLOX検出用モジュールの初期化（weight_pathが指定されていれば）
        self._detector = None
        self._tracker = None
        self._target_selector = None
        if weight_path is not None:
            self._detector = YOLOXDetector(weight_path, score_thr=0.8, nmsthre=0.45)
            self._tracker = ObjectTracker(fps=30.0)
            self._target_selector = AimingTargetSelector(image_center=(640, 360))

        # 新たに、ターゲットとするパネルの指定フラグを追加
        # False → blue_panel (クラス0) / True → red_panel (クラス1)
        self.target_panel = False

        print("init realsense camera")

    @property
    def pipeline_profile(self):
        """RealSenseのパイプラインプロファイルを返すプロパティ"""
        return self._pipeline_profile

    @property
    def is_running(self):
        return self._is_running

    def set_target_panel(self, flag: bool):
        """外部からターゲットパネルフラグを設定する
           False → blue_panel (クラス0)
           True  → red_panel (クラス1)
        """
        self.target_panel = flag

    def start(self):
        """カメラストリームを開始させる"""
        if not self._is_running:
            try:
                print("start realsense stream")
                self._pipeline_profile = self._pipeline.start(self._config)
                self._is_running = True
                # フレーム取得のためのスレッド開始
                self._frame_thread = threading.Thread(target=self.update_frames, daemon=True)
                self._frame_thread.start()
                # 検出スレッド開始（YOLOXによる検出とトラッキング）
                if self._detector is not None:
                    self._detection_thread = threading.Thread(target=self.update_detection, daemon=True)
                    self._detection_thread.start()
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
            if self._frame_thread is not None:
                self._frame_thread.join()
            if self._detection_thread is not None:
                self._detection_thread.join()
            self._pipeline.stop()
            self._config.disable_all_streams()
            self.recorder = None  # Recorderオブジェクトをリセット
        else:
            print("Realsense camera is not running.")

    def update_frames(self):
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

    def update_detection(self):
        """Realsenseカメラから取得した最新のカラー画像に対して、非同期でYOLOX検出とトラッキングを実施するスレッド用メソッド"""
        while self._is_running:
            # 取得した最新のフレームをコピーする
            with self._frame_lock:
                if self._color_frame is None:
                    frame = None
                else:
                    frame = self._color_frame.copy()
            if frame is None:
                time.sleep(0.01)
                continue

            # 物体検出を実施
            detections = self._detector.predict(frame)
            if detections is None:
                detections = []

            # 【ここで target_panel フラグに応じたフィルタリングを実施】
            # robot_state.target_panel が False → blue_panel (クラス0)
            # robot_state.target_panel が True  → red_panel  (クラス1)
            if self.target_panel:
                filtered_detections = [det for det in detections if det[5] == 1]
            else:
                filtered_detections = [det for det in detections if det[5] == 0]

            # フィルタ後の検出結果をtrackerに渡す
            tracked_objects = self._tracker.update(filtered_detections)
            # 照準対象の決定
            aiming_target = self._target_selector.select_target(tracked_objects)

            # 検出結果と照準対象を保存
            with self._detection_lock:
                self._detection_result = tracked_objects
                self._aiming_target = aiming_target

            # 少し待機してから次の検出を実施
            time.sleep(0.01)

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

    def get_detection_results(self):
        """最新の検出結果を取得する"""
        with self._detection_lock:
            return self._detection_result

    def get_aiming_target(self):
        """最新の照準対象を取得する"""
        with self._detection_lock:
            return self._aiming_target

    def draw_detection_results(self, frame, detection_results):
        """検出結果（トラッキング結果）をフレームに描画する"""
        if detection_results is not None:
            self._tracker.draw_boxes(frame, detection_results)
        return frame

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
