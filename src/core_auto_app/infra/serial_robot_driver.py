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

        self._serial: Optional[serial.Serial] = None
        self._open_serial_port()   # Attempt to open once

        # デフォルト状態をセット
        self._robot_state = RobotState()

        # 送受信に排他ロックを使う
        self._serial_lock = Lock()
        self._message_lock = Lock()

        self._pending_message = None

        # スレッド開始
        self._is_closed = False

        # 受信スレッド
        self._recv_thread = Thread(target=self._update_robot_state, daemon=True)
        self._recv_thread.start()

    def _open_serial_port(self) -> None:
        """シリアルポートを開く

        開けなかった場合はNoneをセットする
        """
        try:
            ser = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                stopbits=self._stopbits,
                parity=self._parity,
                timeout=self._timeout,
            )
            if ser.is_open:
                print(f"[SerialRobotDriver] Port opened: {self._port}")
                self._serial = ser
            else:
                print(f"[SerialRobotDriver] Port not actually open: {self._port}")
                self._serial = None
        except serial.serialutil.SerialException as err:
            print(f"[SerialRobotDriver] Failed to open port {self._port}: {err}")
            self._serial = None

    def _update_robot_state(self) -> None:
        """ロボットの状態を取得してメンバ変数を更新する"""
        while not self._is_closed:
            if not (self._serial and self._serial.is_open):
                # ポートがNone or is_open=False
                sleep(1)
                self._open_serial_port()
                continue

            # 改行コード"\n"まで読む
            try:
                with self._serial_lock:
                    buffer = self._serial.readline()
            except serial.serialutil.SerialException as e:
                print(f"[SerialRobotDriver] read error: {e}")
                self._close_port()
                continue
            except Exception as e:
                print(f"[SerialRobotDriver] unknown read error: {e}")
                self._close_port()
                continue

            if not buffer:
                # タイムアウトまたは空
                continue

            # タイムアウトが発生した場合、改行コード"\n"が含まれない
            try:
                str_data = buffer.decode("ascii")
            except UnicodeDecodeError:
                continue
            if "\n" not in str_data:
                continue

            # バッファーをパースする
            try:
                items = str_data.strip().split(",")
                # e.g. "2,120,154,53,25,2,4,0"
                robot_state = RobotState(
                    state_id=RobotStateId(int(items[0])),
                    pitch_deg=float(items[1]) / 10.0,
                    muzzle_velocity=float(items[2]) / 1000.0,
                    reloaded_left_disks=int(items[3]),
                    reloaded_right_disks=int(items[4]),
                    video_id=int(items[5]),
                    auto_aim=bool((int(items[6]) >> 2) & 0b00000001),
                    record_video=bool((int(items[6]) >> 1) & 0b00000001),
                    ready_to_fire=bool((int(items[6]) >> 0) & 0b00000001),
                    reserved=int(items[7]),
                )
                self._robot_state = robot_state
            except (ValueError, IndexError) as err:
                print("[SerialRobotDriver] parse error: ", err)
                continue

    def _send_loop(self):
        while not self._is_closed:
            # 送信文字列を取り出し
            with self._message_lock:
                if self._pending_message:
                    msg = self._pending_message
                    self._pending_message = None
                else:
                    msg = "640,360,0,0\n"  # default

            self._send_data(msg)
            sleep(0.01)

    def _send_data(self, message: str):
        """実際にシリアルに書き込み"""
        if not (self._serial and self._serial.is_open):
            return

        with self._serial_lock:
            try:
                self._serial.write(message.encode())
            except serial.serialutil.SerialException as e:
                print(f"[SerialRobotDriver] write error: {e}")
                self._close_port()
            except Exception as e:
                print(f"[SerialRobotDriver] unknown write error: {e}")
                self._close_port()

    def _close_port(self):
        """ポートを閉じてNoneにする"""
        with self._serial_lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception as e:
                    print("Error closing serial port: ", e)
            self._serial = None

    def set_send_data(self, message: str):
        with self._message_lock:
            self._pending_message = message

    def get_robot_state(self) -> RobotState:
        return deepcopy(self._robot_state)

    def close(self):
        print("closing robot driver")
        self._is_closed = True
        self._recv_thread.join()
        self._send_thread.join()
        self._close_port()
