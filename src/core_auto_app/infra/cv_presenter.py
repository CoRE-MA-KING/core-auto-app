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


class CvPresenter(Presenter):
    def __init__(self):
        # ユーザーがサイズ変更可能な一般的なウィンドウを作成
        cv2.namedWindow("display", cv2.WINDOW_NORMAL)
        # ウィンドウをフルスクリーンに設定
        cv2.setWindowProperty("display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show(self, image: np.array, robot_state: RobotState) -> None:
        """画像をウィンドウに表示する

        Args:
            image: 表示する画像
            robot_state: ロボットの状態

        Note:
            get_ui_command()を呼ばないと表示されないので注意
        """

        STATE_MAP = {
            RobotStateId.UNKNOWN: "不明",
            RobotStateId.INITIALIZING: "初期化",
            RobotStateId.NORMAL: "通常動作",
            RobotStateId.DEFEATED: "撃破",
            RobotStateId.EMERGENCY: "非常停止",
            RobotStateId.COMM_ERROR: "通信エラー",
        }
        state_str = STATE_MAP[robot_state.state_id]

        image = put_outline_text(
            image,
            text=(
                f"状態 {state_str}, "
                f"ピッチ {robot_state.pitch_deg:.1f}°, "
                f"初速 {robot_state.muzzle_velocity:.1f} m/s, "
                f"残弾数 {robot_state.num_disks}"
            ),
            pos=(20, 20),
            size=40,
            color=(255, 255, 255),
        )

        # OpenCVの仕様上、cv2.waitKey()が呼ばれないと表示されない
        cv2.imshow("display", image)

    def get_ui_command(self) -> Command:
        key = cv2.waitKey(10)

        if key == ord("q"):
            return Command.QUIT

        return Command.NONE

    def close(self) -> None:
        print("closing presenter")
        cv2.destroyAllWindows()
