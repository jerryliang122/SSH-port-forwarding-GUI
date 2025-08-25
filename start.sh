#!/bin/bash
# 启动SSH端口转发工具
# 此脚本假设Python已经安装

echo "正在启动Linux SSH端口转发工具..."

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python。请安装Python 3.7+。"
    exit 1
fi

# 检查是否已安装依赖
echo "检查依赖..."
if ! python3 -c "import PyQt5" &> /dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 安装依赖失败。"
        exit 1
    fi
fi

# 启动应用
echo "启动应用..."
python3 src/main.py
if [ $? -ne 0 ]; then
    echo "错误: 应用启动失败。"
    exit 1
fi

exit 0