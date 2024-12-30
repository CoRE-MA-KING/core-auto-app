# core-auto-app

The Championship of Robotics Engineers (CoRE) 向けの、ロボット自動制御を目的としたソフトウェアです。

現時点では自動制御機能はなく、カメラ画像の取得と録画機能のみ実装されています。

# Prerequisites

## Jetson のセットアップ

JetPack 5.1.2 を書き込んだ Jetson AGX Orin で動作を確認しています。
以下の資料を参考に SDK Manager を PC にインストールし、Jetson をセットアップしてください。

- [Getting Started with Jetson AGX Orin Developer Kit](https://developer.nvidia.com/embedded/learn/get-started-jetson-agx-orin-devkit) の Optional Setup Flow
- [NVIDIA SDK Manager Documentation](https://docs.nvidia.com/sdk-manager/)
- [NVIDIA Jetson AGX Orinのセットアップからsdkmanagerでのインストールし直しまで](https://www.souichi.club/deep-learning/jetson-agx-orin/)

# Installation

## リポジトリのクローン

以下のコマンドでこのリポジトリと必要なサブモジュールをクローンします。

```sh
$ git clone --recursive https://github.com/CoRE-MA-KING/core-auto-app.git
$ cd core-auto-app
```

もし `--recursive` を付け忘れた場合は、以下のコマンドでサブモジュールをクローンしてください。

```sh
$ git submodule update --init --recursive
```

## 依存ライブラリのインストール

ライブラリの管理には rye の利用を推奨します。
[Installation](https://rye-up.com/guide/installation/) を参考に rye をインストールしてください。

以下のコマンドで依存ライブラリをインストールしてください。

```sh
$ rye sync
```

なお、Jetson では加えて下記の pyrealsense2 と OpenCV のインストールが必要です。

### pyrealsense2 のインストール

librealsense2 は RealSense カメラの SDK、pyrealsense2 はその Python ラッパーです。
JetPack 5 以降で利用するにはどちらも自前でビルドする必要があります。
以下のコマンドでビルドしてインストールしてください。
librealsense2 はルートに、pyrealsense2 は rye の仮想環境にインストールされます。

```sh
$ cd 3rdparty/librealsense
$ mkdir build && cd build
$ cmake .. \
    -DBUILD_EXAMPLES=true \
    -DCMAKE_BUILD_TYPE=release \
    -DFORCE_RSUSB_BACKEND=false \
    -DBUILD_WITH_CUDA=true \
    -DBUILD_PYTHON_BINDINGS:bool=true \
    -DPYTHON_INSTALL_DIR=$PWD/../../../.venv/lib/python3.8/site-packages
$ make -j$(($(nproc)-1))
$ sudo make install
```

### OpenCV のインストール

Jetson では SDK Manager によって OpenCV がインストールされますが、そのままでは rye の仮想環境からは利用できません。
以下のコマンドでリンクを作成してください。

```sh
$ cd ../../../
$ ln -s /usr/lib/python3.8/dist-packages/cv2 .venv/lib/python3.8/site-packages/cv2
```

### YOLOXとその依存関係のインストール

ダメージパネルの物体認識のためにYOLOXを使用します。少々特殊な環境であるため、パッケージを含めて手動でインストールします。一部のパッケージはソースビルドが必要です。

#### torchののインストール

```sh
# 周辺ツールをインストール
$ sudo apt install autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons python3-pip libopenblas-dev

# インストールしたいバージョン（JetPackのバージョンに依存）に合わせた環境変数を設定（今回はJetPack5）
$ export TORCH_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl

$ python3 -m pip install --upgrade pip
$ python3 -m pip install aiohttp numpy=='1.24.4' scipy=='1.5.3'
$ export "LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH"
$ python3 -m pip install --upgrade protobuf
$ python3 -m pip install --no-cache $TORCH_INSTALL
```

#### torchvisionのインストール

```sh
$ sudo apt install libjpeg-dev zlib1g-dev libpython3-dev libopenblas-dev libavcodec-dev libavformat-dev libswscale-dev
$ git submodule update --init --recursive
$ cd 3rdparty/torchvision
#$ git checkout <任意のバージョン>  # 任意のバージョンにチェックアウトデフォルトではJetPack5に対応した0.16でサブモジュール登録済み
$ export BUILD_VERSION=0.16.1  # インストール対象バージョンに合わせた環境変数の指定
$ python3 setup.py install # --userをつけてしまうと"~/.local/"配下にインストールされるので注意
```

#### onnx-simplifier(onnxsim)のインストール

onnxsimはpipでのインストールに引っかかりやすいので、以下のコマンドでビルドとインストールを実行し、Pythonパッケージとして登録します。

```sh
$ git submodule update --init --recursive
$ cd 3rdparty/onnx-simplifier
$ pip3 install -r requirements.txt
$ mkdir build && cd build
$ cmake .. -DCMAKE_BUILD_TYPE=Release
$ make -j$(nproc)
$ cd ../
$ pip3 instlal .
```

#### YOLOXのインストール

依存関係のツールが準備できたら、YOLOXをインストールします。

本家YOLOXのリポジトリからForkしてJetson（JetPack5）に少しカスタマイズしています。`PEP 517`の処理フローの関係で`pip3 install -v -e .`ではなく`python3 setup.py develop`でインストールを実行します。

```sh
$ git submodule update --init --recursive
$ cd 3rdparty/YOLOX
$ python3 setup.py develop  # "pip3 install -v -e ."はNG
```

# Usage

以下のコマンドで rye の仮想環境でアプリケーションを起動できます。
`--robot_port` オプションでマイコンとの通信に使用するシリアルポートを指定してください。
起動後は `q` キーで終了します。

```sh
$ rye run core_auto_app --robot_port=/dev/ttyUSB0
```

`--record_dir` オプションで録画の保存先のディレクトリを指定してください。ファイル名は `camera_<起動日時>.bag` になります。

```sh
$ rye run core_auto_app --record_dir=/mnt/ssd1
```

なお、以下のように直接 venv の仮想環境に入って起動することも可能です。

```sh
$ source .venv/bin/activate
$ core_auto_app
```

# 自動起動の設定

PCの起動時に、自動的にアプリケーションを実行するには、以下のようなファイルを作成してください。

```sh
$ vim ~/.config/autostart/core-auto-app.desktop
[Desktop Entry]
Name=run core auto app
Exec=/home/nvidia/core_auto_app/scripts/autostart.sh
Type=Application
```

