from copy import deepcopy
from threading import Thread, Lock
from time import sleep
from typing import Optional

import serial

from core_auto_app.application.interfaces import RobotDriver
from core_auto_app.domain.messages import RobotStateId, RobotState


class SerialRobotDriver(RobotDriver):
    """マイコンと通信しロボットを制御するクラス

    Args:
        port: シリアルポートのデバイス
        baudrate: ボーレート
        timeout: readのタイムアウト[秒]
    """

    def __init__(
        self,
        port,
        baudrate=115200,
        # baudrate=921600,
        parity=serial.PARITY_NONE,
        # parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        timeout=1.0,
    ):
        # シリアルポートを開く
        self._port = port
        self._baudrate = baudrate
        self._parity = parity
        self._stopbits = stopbits
        self._timeout = timeout
        self._port: Optional[serial.Serial]
        self._open_serial_port()

        # デフォルト状態をセット
        self._robot_state = RobotState()

        # 送受信に排他ロックを使う
        self._serial_lock = Lock()

        # スレッド開始
        self._is_closed = False
        self._thread = Thread(target=self._update_robot_state)
        self._thread.start()

    def _open_serial_port(self) -> None:
        """シリアルポートを開く

        開けなかった場合はNoneをセットする
        """
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                stopbits=self._stopbits,
                parity=self._parity,
                timeout=self._timeout,
            )
        except serial.serialutil.SerialException as err:
            print(err)
            self._serial = None

    def _update_robot_state(self) -> None:
        """ロボットの状態を取得してメンバ変数を更新する"""
        while not self._is_closed:
            # シリアルポートが開いていなければ1秒待って開く
            if not self._serial:
                sleep(1)
                self._open_serial_port()
                continue

            # 改行コード"\n"まで読む
            try:
                with self._serial_lock:
                    # buffer = "2,2,3,4,5,1,4,0"  # テスト時のダミー
                    buffer = self._serial.readline()
                print(f"read state: {buffer}")

            except Exception as err:
                print(err)
                self._serial.close()
                self._serial = None
                continue

            # タイムアウトが発生した場合、改行コード"\n"が含まれない
            try:
                # str_data = buffer  # テスト時のダミー
                str_data = buffer.decode("ascii")

            except UnicodeDecodeError as err:
                print(err)
                continue
            if "\n" not in str_data:
                continue

            # バッファーをパースする
            try:
                str_data = str_data.replace("\n", "")
                str_data = str_data.split(",")

                robot_state = RobotState(
                    state_id=RobotStateId(int(str_data[0])),
                    pitch_deg=float(str_data[1]) / 10.0,  # 1/10deg
                    muzzle_velocity=float(str_data[2]) / 1000,  # m/s
                    reloaded_left_disks=int(str_data[3]),  # 枚
                    reloaded_right_disks=int(str_data[4]),  # 枚
                    video_id=int(str_data[5]),  # カメラID
                    # "str_data[6]"は複数のflagをまとめたバイト
                    auto_aim=bool((int(str_data[6]) >> 2) & 0b00000001),  # 自動照準フラグ
                    record_video=bool((int(str_data[6]) >> 1) & 0b00000001),  # 録画フラグ
                    ready_to_fire=bool((int(str_data[6]) >> 0) & 0b00000001),  # 射出可否フラグ
                    reserved=int(str_data[7])  # 未使用
                )

                # 状態を更新
                self._robot_state = robot_state

            except ValueError as err:
                print("Could not parse")
                print(err)
                continue

    def get_robot_state(self) -> RobotState:
        """最新のロボットの状態を返す"""
        return deepcopy(self._robot_state)

    def send_data(self, message: str) -> None:
        """
        ユーザが任意のタイミングで呼び出す送信用メソッド
        Args:
            message: 送信する文字列(末尾に"\n"などをつけるかは呼び出し側で決める)
        """
        if not self._serial:
            return
        with self._serial_lock:
            try:
                self._serial.write(message.encode())
            except Exception as e:
                print(f"Serial write error: {e}")

    def close(self):
        print("closing robot driver")
        self._is_closed = True
        self._thread.join()
        if self._serial:
            self._serial.close()
