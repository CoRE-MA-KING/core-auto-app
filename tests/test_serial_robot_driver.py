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
    "buffer, expected_robot_state",
    [
        (
            b"0,0.1,10.0\n",
            RobotState(state_id=RobotStateId(0), pitch_deg=0.1, muzzle_velocity=10.0),
        ),
    ],
)
def test_get_robot_state(pty, buffer, expected_robot_state):
    """ロボットの状態を取得するテスト"""
    port0, port1 = pty

    with Serial(port0, 9600) as ser, SerialRobotDriver(port1, 9600) as driver:
        ser.write(buffer)
        ser.flush()  # wait until all data is written

        # 別スレッドで状態を読み込むので更新されるまで待機
        time.sleep(0.1)
        robot_state = driver.get_robot_state()

        assert robot_state == expected_robot_state
