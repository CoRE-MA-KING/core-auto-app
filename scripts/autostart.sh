#!/usr/bin/bash

set -e

cd /home/nvidia/core_auto_app
source .venv/bin/activate

# # 解像度変更
# xrandr --output DP-0 --mode 1280x720
# 一度モニタをオフにする
monitor=$(xrandr --query | grep " connected" | awk '{print $1}')
sleep 1  # 1秒待機
echo $monitor
# モニタをオンにして解像度を設定する（1920x1080, リフレッシュレート60Hz）
sleep 1  # 1秒待機

xrandr --output "$monitor" --mode 1920x1080

# 仮想シリアルポートを使用しないアプリケーションの起動
core_auto_app --robot_port=/dev/ttyUSB0
