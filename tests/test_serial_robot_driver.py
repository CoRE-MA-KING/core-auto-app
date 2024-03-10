import os
import pytest
from serial import Serial
import subprocess
import time

from core_auto_app.domain.messages import RobotStateId, RobotState
from core_auto_app.infra.serial_robot_driver import SerialRobotDriver


@pytest.fixture()
def pty(tmp_path):
    """仮想シリアルポート(pseudo-teletype)を返すフィクスチャ"""
    port0 = str(tmp_path / "vtty0")
    port1 = str(tmp_path / "vtty1")

    # socatでポートを作成
    proc = subprocess.Popen(
        f"socat -d -d pty,raw,echo=0,link={port0} pty,raw,echo=0,link={port1}".split()
    )

    try:
        # ポートが作成されるまで待機
        while not os.path.exists(port0) or not os.path.exists(port1):
            pass

        yield port0, port1

    finally:
        # socatのプロセスを停止
        proc.terminate()
        proc.wait()


def test_virtual_serial_port(pty):
    """仮想シリアルポートのテスト"""
    port0, port1 = pty

    with Serial(port0, 9600) as ser0, Serial(port1, 9600) as ser1:
        ser0.write(b"hoge fuga\n")
        received_data = ser1.readline()  # 改行コードまで読む
        assert received_data.decode("utf-8") == "hoge fuga\n"


@pytest.mark.parametrize(
    "buffer, expected_robot_state_id",
    [
        (b"0,0,0,0,0,0,0,0\n", RobotStateId.UNKNOWN,),
        (b"1,0,0,0,0,0,0,0\n", RobotStateId.INITIALIZING,),
        (b"2,0,0,0,0,0,0,0\n", RobotStateId.NORMAL,),
        (b"3,0,0,0,0,0,0,0\n", RobotStateId.DEFEATED,),
        (b"4,0,0,0,0,0,0,0\n", RobotStateId.EMERGENCY,),
        (b"5,0,0,0,0,0,0,0\n", RobotStateId.COMM_ERROR,),
    ],
)
def test_get_robot_state_id(pty, buffer, expected_robot_state_id):
    """ロボットの状態IDを取得するテスト"""
    port0, port1 = pty

    with Serial(port0, 921600) as ser, SerialRobotDriver(port1, 921600) as driver:
        ser.write(buffer)
        ser.flush()  # wait until all data is written

        # 別スレッドで状態を読み込むので更新されるまで待機
        time.sleep(0.1)
        robot_state = driver.get_robot_state()

        assert robot_state.state_id == expected_robot_state_id


@pytest.mark.parametrize(
    "buffer, expected_robot_state",
    [
        (b"0,1,0,0,0,0,0,0\n", RobotState(ready_to_fire=True),),
        (b"0,0,1,0,0,0,0,0\n", RobotState(pitch_deg=0.1),),
        (b"0,0,0,1,0,0,0,0\n", RobotState(muzzle_velocity=1),),
        (b"0,0,0,0,1,0,0,0\n", RobotState(record_video=1),),
        (b"0,0,0,0,0,1,0,0\n", RobotState(reboot_pc=1),),
    ],
)
def test_get_robot_other_states(pty, buffer, expected_robot_state):
    """ロボットの状態IDを取得するテスト"""
    port0, port1 = pty

    with Serial(port0, 921600) as ser, SerialRobotDriver(port1, 921600) as driver:
        ser.write(buffer)
        ser.flush()  # wait until all data is written

        # 別スレッドで状態を読み込むので更新されるまで待機
        time.sleep(0.1)
        robot_state = driver.get_robot_state()

        assert robot_state == expected_robot_state

