
from copy import deepcopy
from threading import Lock, Thread
from serial import Serial

from core_auto_app.application.interfaces import RobotDriver
from core_auto_app.domain.messages import RobotStateId, RobotState


class SerialRobotDriver(RobotDriver):
    """マイコンと通信しロボットを制御するクラス

    Args:
        port: シリアルポートのデバイス
        baudrate: ボーレート
        timeout: readのタイムアウト[秒]
    """

    def __init__(self, port, baudrate, timeout=1.0):
        # シリアルポートを開く
        self._serial = Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

        # デフォルト状態をセット
        self._robot_state = RobotState()

        # スレッド開始
        self._is_closed = False
        self._thread = Thread(target=self._update_robot_state)
        self._thread.start()

    def _update_robot_state(self) -> None:
        """ロボットの状態を取得してメンバ変数を更新する"""
        while not self._is_closed:
            # 改行コード"\n"まで読む
            buffer = self._serial.readline()

            # タイムアウトが発生した場合、改行コード"\n"が含まれない
            str_data = buffer.decode("utf-8")
            if "\n" not in str_data:
                continue

            # バッファーをパースする
            str_data = str_data.replace("\n", "")
            str_data = str_data.split(",")
            robot_state = RobotState(
                state_id=RobotStateId(int(str_data[0])),
                pitch_deg=float(str_data[1]),
                muzzle_velocity=float(str_data[2]),
            )

            # 状態を更新
            self._robot_state = robot_state

    def get_robot_state(self) -> RobotState:
        """最新のロボットの状態を返す"""
        return deepcopy(self._robot_state)

    def close(self):
        self._is_closed = True
        self._thread.join()
        self._serial.close()
