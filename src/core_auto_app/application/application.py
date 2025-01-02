from core_auto_app.application.interfaces import (
    ApplicationInterface,
    ColorCamera,
    Camera,
    Presenter,
    RobotDriver,
)
from core_auto_app.domain.messages import Command
from core_auto_app.detector.object_detector import YOLOXDetector  # YOLOXの物体検出用クラス
from core_auto_app.detector.tracker_utils import ObjectTracker  # トラッキング用クラス
from core_auto_app.detector.aiming.aiming_service import AimingService  # 照準用クラス
import pyrealsense2 as rs
import cv2


class Application(ApplicationInterface):
    """Implementation for the CoRE auto-pilot application."""

    def __init__(
        self,
        realsense_camera: Camera,
        a_camera: ColorCamera,
        b_camera: ColorCamera,
        presenter: Presenter,
        robot_driver: RobotDriver,
        weight_path: str  # コマンドライン引数で渡すモデルファイルパス
    ):
        self._realsense_camera = realsense_camera
        self._a_camera = a_camera
        self._b_camera = b_camera
        self._presenter = presenter
        self._robot_driver = robot_driver

        self._is_recording = False

        # YOLOXの物体検出初期化
        # weight_pathはmain.pyから受け取ったpthファイルのパス
        # ここでスコアしきい値(score_thr)やNMSしきい値(nmsthre)も調整可能
        self._detector = YOLOXDetector(weight_path, score_thr=0.8, nmsthre=0.45)

        # トラッキング初期化
        self._tracker = ObjectTracker(fps=30.0)

        # RealSenseCamera起動後に pipeline_profileが決まる想定
        # ここでは None で初期化し、spin()の最初あたりでセット
        self._aiming_service = None

    def spin(self):
        self._a_camera.start()
        self._b_camera.start()
        self._realsense_camera.start()

        # RealSenseCameraが start() した後なら pipeline_profile 取得可能
        pipeline_profile = self._realsense_camera.pipeline_profile
        # RealSenseCameraからのパラメータを取得
        intrinsics = pipeline_profile.get_stream(rs.stream.depth).as_video_stream_profile().get_intrinsics()
        
        # カメラのオフセット(ロボット中心→カメラ原点まで) [m]（ひとまず今はすべて0.0）
        camera_offset = (0.0, 0.0, 0.0)  # [m]単位で指定 例: 前方20cm, 上方30cmだと(0.2, 0.3, 0.0)
        self._aiming_service = AimingService(intrinsics, camera_offset)
        
        while True:
            # ロボットの状態取得
            robot_state = self._robot_driver.get_robot_state()
            # 録画設定の更新
            if robot_state.record_video and not self._is_recording:
                self._realsense_camera.start_recording()
                self._is_recording = True
            elif not robot_state.record_video and self._is_recording:
                self._realsense_camera.stop_recording()
                self._is_recording = False

            # カメラ画像取得
            if robot_state.video_id == 0:
                color = self._a_camera.get_image()
            elif robot_state.video_id == 1:
                color = self._b_camera.get_image()
            elif robot_state.video_id == 2:
                color, depth = self._realsense_camera.get_images()
                if color is not None:
                    # YOLOXで物体を検出  detections: [(x1, y1, x2, y2, score, cls_id), ...]
                    detections = self._detector.predict(color)
                    # 検出結果を描画（物体検出の結果）
                    # self._detector.draw_boxes(color, detections)

                    # トラッキング  racked_objects: [(x1, y1, x2, y2, track_id), ...]
                    tracked_objects = self._tracker.update(detections)
                    # 検出結果を描画（トラッキングの結果）
                    self._tracker.draw_boxes(color, tracked_objects)

                    # 3次元座標取得
                    obj_3d_list = self._aiming_service.compute_object_coordinates(depth, tracked_objects)
                    # 画面に3D情報を表示
                    self._aiming_service.draw_3d_info(color, obj_3d_list)

                    ### 以下の処理は射出口の仰角計算の際に使用するかも
                    # 仰角を計算する例（ここでは1つ目の物体だけ狙う想定）
                    # if len(obj_3d_list) > 0:
                    #     t_id, X, Y, Z = obj_3d_list[0]
                    #     angle_deg = self._aiming_service.compute_aim_angle(X, Y, Z)
                    #     # 何らかの処理... 例えば表示
                    #     cv2.putText(color, f"AimAngle: {angle_deg:.1f} deg", (450, 50),
                    #                 cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0), 2)

            else:
                color = self._a_camera.get_image()  # デフォルトでカメラAの画像

            if color is None:
                color = self._a_camera.get_image()  # 取得できなかった場合はカメラAの画像

            # 描画 (ここの指定によって画像の質が変わりそう)
            self._presenter.show(color, robot_state)
            command = self._presenter.get_ui_command()

            if command == Command.QUIT:
                break

        # アプリケーション終了時にカメラを停止
        self._realsense_camera.close()
        self._a_camera.close()
        self._b_camera.close()
