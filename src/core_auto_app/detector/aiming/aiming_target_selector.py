# detector/aiming_target_selector.py

import math
import cv2

class AimingTargetSelector:
    """
    トラッキング結果 (x1, y1, x2, y2, track_id) のリストから、
    照準対象の物体を決定するクラス。

    - 画像中心 (640, 360) とのピクセル距離が最小の物体を優先
    - 距離が同じ場合は前フレームの対象IDを優先
    - それでも複数なら横幅が大きい方を優先
    - select_target(...) で決定したtargetをメンバ変数として保持
    - draw_aiming_target_info(...) で画面に描画できる
    """

    def __init__(self, image_center=(640, 360)):
        self.image_center = image_center
        self.prev_target_id = None   # 前フレームで選択されたID
        self.aiming_target = None    # (cx, cy) 現在の照準対象座標
        self.current_target_id = None  # 現在の照準対象ID

    def select_target(self, tracked_objects):
        """
        Args:
            tracked_objects: [(x1, y1, x2, y2, track_id), ...]

        Returns:
            aiming_target: (cx, cy) or None
        """
        if not tracked_objects:
            self.aiming_target = None
            self.current_target_id = None
            return None

        center_x, center_y = self.image_center

        # 1) 物体ごとの距離、幅などをまとめる
        obj_list = []
        for (x1, y1, x2, y2, t_id) in tracked_objects:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            dx = cx - center_x
            dy = cy - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            width = (x2 - x1)

            obj_list.append({
                't_id': t_id,
                'cx': cx,
                'cy': cy,
                'dist': distance,
                'width': width
            })

        # 2) 最小距離を持つ物体を抽出
        min_dist = min(o['dist'] for o in obj_list)
        tie_list = [o for o in obj_list if abs(o['dist'] - min_dist) < 1e-9]

        if len(tie_list) == 1:
            chosen = tie_list[0]
        else:
            # 3) tie_list の中で prev_target_id を含むものがあればそれを優先
            tie_list_id_match = [o for o in tie_list if o['t_id'] == self.prev_target_id]
            if len(tie_list_id_match) == 1:
                chosen = tie_list_id_match[0]
            elif len(tie_list_id_match) > 1:
                # 4) width大きい方
                chosen = max(tie_list_id_match, key=lambda x: x['width'])
            else:
                chosen = max(tie_list, key=lambda x: x['width'])

        self.prev_target_id = chosen['t_id']
        self.current_target_id = chosen['t_id']
        self.aiming_target = (chosen['cx'], chosen['cy'])

        return self.aiming_target

    def draw_aiming_target_info(self, frame):
        """
        現在の照準対象IDと座標を画面左上に描画
        """
        if self.aiming_target is not None and self.current_target_id is not None:
            (cx, cy) = self.aiming_target
            target_id = self.current_target_id
            txt = f"Target ID:{target_id} center=({cx},{cy})"
            # 左上(20,50)に表示 (お好みで位置を調整)
            cv2.putText(frame, txt, (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
