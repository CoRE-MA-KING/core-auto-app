#!/usr/bin/bash
set -e

# 1. Jetsonのクロックを最大にする
sudo jetson_clocks

# 2. CPUガバナーをperformanceモードに設定
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    echo "performance" | sudo tee $cpu/cpufreq/scaling_governor
done

# 3. 不要なサービスを停止（例: コンポジタやバックグラウンドアプリがあれば）
# sudo systemctl stop some_service

# 4. xrandrでディスプレイ出力の設定（前述のスクリプト内容を利用）
monitor=$(xrandr --query | grep " connected" | awk '{print $1}' | head -n 1)
if [ -z "$monitor" ]; then
    echo "No connected monitor found. Exiting."
    exit 1
fi
echo "Detected monitor: $monitor"
xrandr --output "$monitor" --off
sleep 2
xrandr --output "$monitor" --mode 1280x720 --rate 30
xset dpms force on
sleep 1

cd /home/nvidia/core_auto_app
source .venv/bin/activate

core_auto_app --robot_port=/dev/ttyUSB0
