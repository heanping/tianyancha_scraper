#!/bin/bash
# Linux/Mac启动脚本 - 天眼查爬虫

echo "================================"
echo "天眼查爬虫启动脚本"
echo "================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3环境"
    echo "请先安装Python: https://www.python.org/"
    exit 1
fi

echo "✓ Python环境检测成功"
echo ""

# 激活虚拟环境（优先 .venv，其次 venv）
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "正在创建虚拟环境 (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 检查依赖
echo "检查依赖包..."
pip list | grep -q selenium
if [ $? -ne 0 ]; then
    echo "正在安装依赖包..."
    pip install -r requirements.txt
else
    echo "✓ 依赖包已安装"
fi

echo ""
echo "使用Edge浏览器..."
python main.py edge

deactivate
