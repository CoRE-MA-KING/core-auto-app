#!/usr/bin/bash

set -e

cd /home/nvidia/core_auto_app
source .venv/bin/activate

# 解像度変更
xrandr --output DP-1 --mode 1280x720

# 仮想シリアルポートを使用しないアプリケーションの起動
core_auto_app --robot_port=/dev/ttyUSB0 --record_dir=/mnt/ssd1
