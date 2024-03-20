#!/usr/bin/bash

set -e

cd /home/nvidia/core_auto_app
source .venv/bin/activate

# 仮想シリアルポートを使用しないアプリケーションの起動
core_auto_app --robot_port=/dev/ttyUSB0

