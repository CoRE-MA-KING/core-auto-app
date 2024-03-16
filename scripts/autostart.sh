#!/usr/bin/bash

set -e

cd /home/nvidia/core_auto_app
source .venv/bin/activate

# # 開発用に仮想シリアルポート使用
# socat -d -d pty,raw,echo=0,link=/tmp/vtty0 pty,raw,echo=0,link=/tmp/vtty1 &
# core_auto_app --robot_port=/tmp/vtty0

# 仮想シリアルポートを使用しないアプリケーションの起動
core_auto_app --robot_port=/tmp/ttyUSB0

