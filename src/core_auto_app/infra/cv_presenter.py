import cv2
import numpy as np

from core_auto_app.application.interfaces import Presenter
from core_auto_app.domain.messages import Command


class CvPresenter(Presenter):
    def __init__(self):
        # ユーザーがサイズ変更可能な一般的なウィンドウを作成
        cv2.namedWindow("display", cv2.WINDOW_NORMAL)
        # ウィンドウをフルスクリーンに設定
        cv2.setWindowProperty("display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show(self, image: np.array) -> None:
        """画像をウィンドウに表示する

        Args:
            image: 表示する画像

        Note:
            get_ui_command()を呼ばないと表示されないので注意
        """
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
