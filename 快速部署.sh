#!/bin/bash

echo "========================================"
echo "阀门报价系统 - 快速部署脚本"
echo "========================================"
echo

# 检查Python是否安装
echo "[1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python 3.8+"
    exit 1
fi
echo "✅ Python环境检查通过"

# 检查pip是否可用
echo "[2/5] 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3不可用，请检查Python安装"
    exit 1
fi
echo "✅ pip检查通过"

# 安装依赖
echo "[3/5] 安装Python依赖..."
cd backend
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi
echo "✅ 依赖安装完成"

# 测试OCR功能
echo "[4/5] 测试OCR功能..."
python3 ocr_config.py
if [ $? -ne 0 ]; then
    echo "❌ OCR功能测试失败"
    echo "请检查tupian目录是否完整"
    exit 1
fi
echo "✅ OCR功能测试通过"

# 启动服务
echo "[5/5] 启动服务..."
echo
echo "🚀 正在启动后端服务..."
cd backend
python3 main.py &
BACKEND_PID=$!

echo "🚀 正在启动前端服务..."
cd ../frontend
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo
echo "📱 访问地址: http://localhost:8000"
echo "👤 默认账号: admin"
echo "🔑 默认密码: admin123"
echo
echo "💡 提示："
echo "- 后端服务运行在端口 8001 (PID: $BACKEND_PID)"
echo "- 前端服务运行在端口 8000 (PID: $FRONTEND_PID)"
echo "- 按 Ctrl+C 停止服务"
echo

# 等待用户中断
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 