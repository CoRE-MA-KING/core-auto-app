from typing import Optional

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image

from core_auto_app.application.interfaces import Presenter
from core_auto_app.domain.messages import Command, RobotStateId, RobotState

def put_text(img, text, pos, size, color):
    """日本語フォントを画面に描画する関数"""
    font = ImageFont.truetype(
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        size,
    )
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, fill=color, font=font)
    return np.array(img_pil)


def put_outline_text(img, text, pos, size, color, shadow_color="black"):
    """フチ付き文字を表示する関数"""
    for vec in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        new_pos = (pos[0] + vec[0], pos[1] + vec[1])
        img = put_text(img, text, new_pos, size, shadow_color)
    return put_text(img, text, pos, size, color)


def draw_crosshair(img, pos, color, shadow_color=None):
    """十字マークを表示する関数"""
    if not shadow_color:
        shadow_color = (0, 0, 0)

    img = cv2.line(
        img, (pos[0], pos[1] - 12), (pos[0], pos[1] + 12), shadow_color, thickness=4
    )
    img = cv2.line(
        img, (pos[0] - 12, pos[1]), (pos[0] + 12, pos[1]), shadow_color, thickness=4
    )
    img = cv2.line(
        img, (pos[0], pos[1] - 10), (pos[0], pos[1] + 10), color, thickness=2
    )
    img = cv2.line(
        img, (pos[0] - 10, pos[1]), (pos[0] + 10, pos[1]), color, thickness=2
    )
    return img


class CvPresenter(Presenter):
    def __init__(self):
        # ユーザーがサイズ変更可能な一般的なウィンドウを作成
        cv2.namedWindow("display", cv2.WINDOW_NORMAL)
        # ウィンドウをフルスクリーンに設定
        cv2.setWindowProperty("display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show(self, image: Optional[np.array], robot_state: RobotState) -> None:
        """画像をウィンドウに表示する

        Args:
            image: 表示する画像
            robot_state: ロボットの状態

        Note:
            get_ui_command()を呼ばないと表示されないので注意
        """

        STATE_MAP = {
            RobotStateId.UNKNOWN: "Unknown",
            RobotStateId.INITIALIZING: "Init",
            RobotStateId.NORMAL: "Normal",
            RobotStateId.DEFEATED: "Destoryed",
            RobotStateId.EMERGENCY: "EmergencyStop",
            RobotStateId.COMM_ERROR: "CommuError",
        }
        state_str = STATE_MAP[robot_state.state_id]

        # 入力画像がない場合、黒画像を表示する
        if image is None:
            image = np.zeros((720, 1280, 3), dtype=np.uint8)

        # left_disk_color=(255, 255, 255)
        # if robot_state.reloaded_left_disks <= 5:
        #     left_disk_color=(0, 0, 255)

        # right_disk_color=(255, 255, 255)
        # if robot_state.reloaded_right_disks <= 5:
        #     right_disk_color=(0, 0, 255)

        record_txt = ""
        if robot_state.record_video:
            record_txt = "(REC)"

        auto_aim_str = "Manual"
        if robot_state.auto_aim:
            auto_aim_str = "Auto Aim"

        # cv2.putText(image, "ABCxyz", (300, 630), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,255,255))

        cv2.putText(image,
                    f"[Disk]L:{robot_state.reloaded_left_disks:>2}/R:{robot_state.reloaded_right_disks:>2} [Deg]:{robot_state.pitch_deg:5.1f} [State]:{state_str:<14} {record_txt}", (300, 690), cv2.FONT_HERSHEY_DUPLEX, 1.0, color=(255, 255, 255), thickness=2)

        # # まとめて文字列を表示　
        # image = put_outline_text(ssss
        #     image, text=f"【残弾】　(左){robot_state.reloaded_left_disks}　(右){robot_state.reloaded_right_disks}\n"s
        #                 f"【ピッチ】{robot_state.pitch_deg:.1f}° 【射出速度】 {robot_state.muzzle_velocity:.1f}m/s　　　　【状態】{state_str} {record_txt}",
        #     pos=(300, 630), size=30, color=(255, 255, 255)
        # )

        # # 十字を表示q
        # image = draw_crosshair(
        #     image, (image.shape[1] // 2, image.shape[0] // 2), (0, 255, 255)
        # )

        # OpenCVの仕様上、cv2.waitKey()が呼ばれないと表示されない
        cv2.imshow("display", image)

    def get_ui_command(self) -> Command:
        key = cv2.waitKey(1)

        if key == ord("q"):
            return Command.QUIT

        return Command.NONE

    def recreate_window(self):
        cv2.destroyWindow("display")
        cv2.namedWindow("display", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def close(self) -> None:
        print("closing presenter")
        cv2.destroyAllWindows()
