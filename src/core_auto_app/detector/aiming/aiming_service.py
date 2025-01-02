import pyrealsense2 as rs
import numpy as np
import cv2
from typing import List, Tuple

class AimingService:
    """
    トラッキング結果と深度画像から、物体の3次元座標を計算し、
    ロボット中心座標系への変換や可視化（ID + x,y,z表示）を行うクラス。

    想定する座標系:
      - RealSenseの座標系 (rs.rs2_deproject_pixel_to_point) → カメラ座標
      - ロボットの中心座標系 (0,0,0) との差は camera_offset_x,y,z で吸収
    """

    def __init__(
        self, 
        intrinsics: rs.intrinsics, 
        camera_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ):
        """
        Args:
            intrinsics: RealSenseのDepthストリームから取得したカメラ内部パラメータ
            camera_offset: (x, y, z) [m] カメラ原点とロボット中心のズレ
                例: カメラがロボット前方20cm, 上方30cm, 右側0cm の位置にある場合
                camera_offset = (0.2, 0.3, 0.0)
        """
        self._intrinsics = intrinsics
        self._camera_offset = camera_offset

    def compute_3d(self, depth_image: np.ndarray, x: int, y: int) -> Tuple[float, float, float]:
        """
        バウンディングボックス中心ピクセル(x, y)の3次元座標を取得 (カメラ座標系 → ロボット座標系)
        戻り値: (X, Y, Z) [m], ロボット座標系での座標
        """
        if not (0 <= y < depth_image.shape[0] and 0 <= x < depth_image.shape[1]):
            # 範囲外の場合は(0,0,0)などの初期値を返す
            return (0.0, 0.0, 0.0)

        depth_value = depth_image[y, x]
        # RealSenseのdepth_valueはミリメートル単位を想定
        if depth_value == 0:
            # 無効ピクセル
            return (0.0, 0.0, 0.0)

        distance_m = float(depth_value) / 1000.0  # mm → m

        # RealSenseのdeprojectを使ってカメラ座標系の3D点取得
        point_3d = rs.rs2_deproject_pixel_to_point(
            self._intrinsics, [x, y], distance_m
        )
        # point_3d = [Xc, Yc, Zc] (カメラ座標系, m)

        # カメラ座標系 → ロボット中心座標系への平行移動 (回転などは省略例)
        # 例：ロボット中心(0,0,0)とカメラ原点が offset=(0.2,0.3,0.0) [m]離れていると想定
        Xr = point_3d[0] + self._camera_offset[0]
        Yr = point_3d[1] + self._camera_offset[1]
        Zr = point_3d[2] + self._camera_offset[2]

        return (Xr, Yr, Zr)

    def compute_object_coordinates(
        self,
        depth_image: np.ndarray,
        tracked_objects: List[Tuple[int, int, int, int, int]]
    ) -> List[Tuple[int, float, float, float]]:
        """
        トラッキングされたオブジェクト群からID + 3次元座標を計算
        Args:
            depth_image: RealSenseのdepth配列 (aligned to color)
            tracked_objects: [(x1, y1, x2, y2, track_id), ...]

        Returns:
            result: [(track_id, X, Y, Z), ...] 各オブジェクトの3D座標[m]
        """
        results = []
        for (x1, y1, x2, y2, t_id) in tracked_objects:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            X, Y, Z = self.compute_3d(depth_image, cx, cy)
            results.append((t_id, X, Y, Z))

        return results

    def draw_3d_info(
        self,
        frame: np.ndarray,
        object_3d_list: List[Tuple[int, float, float, float]]
    ) -> None:
        """
        トラッキングID + (X, Y, Z)情報をフレームに描画
        Args:
            frame: カラー画像
            object_3d_list: [(track_id, X, Y, Z), ...]
        """
        for (track_id, X, Y, Z) in object_3d_list:
            # 可視化の位置は任意（ここでは適当に左上に並べる例）
            txt = f"ID:{track_id} (X={X:.2f} Y={Y:.2f} Z={Z:.2f})"
            cv2.putText(frame, txt, (20, 40 + track_id * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

    # もし射出口からの仰角計算など行う場合:
    def compute_aim_angle(self, X: float, Y: float, Z: float) -> float:
        """
        例: 対象物体までの(X,Y,Z)を使い、仰角を計算する。簡単化した例。
        (ロボット中心→射出口のオフセットや、重力・弾道などは実装次第)
        戻り値: 仰角 [deg] など
        """
        # ここでは例としてZが奥行き(前方方向), Yが垂直方向, Xが水平方向と仮定:
        # 単純に「距離」と「高さY」の比から仰角を計算
        dist_xy = np.hypot(X, Z)  # 水平方向距離
        if dist_xy == 0:
            return 0.0
        angle_rad = np.arctan2(Y, dist_xy)
        angle_deg = np.degrees(angle_rad)
        return angle_deg
