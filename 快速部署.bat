@echo off
chcp 65001 >nul
echo ========================================
echo 阀门报价系统 - 快速部署脚本
echo ========================================
echo.

:: 检查Python是否安装
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

:: 检查pip是否可用
echo [2/5] 检查pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip不可用，请检查Python安装
    pause
    exit /b 1
)
echo ✅ pip检查通过

:: 安装依赖
echo [3/5] 安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败，请检查网络或pip配置
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

:: 测试OCR功能
echo [4/5] 测试OCR功能...
python ocr_config.py
if errorlevel 1 (
    echo ❌ OCR功能测试失败
    echo 请检查tupian目录是否完整
    pause
    exit /b 1
)
echo ✅ OCR功能测试通过

:: 启动服务
echo [5/5] 启动服务...
echo.
echo 🚀 正在启动后端服务...
start "后端服务" cmd /k "cd backend && python main.py"

echo 🚀 正在启动前端服务...
start "前端服务" cmd /k "cd frontend && python -m http.server 8000"

echo.
echo ========================================
echo ✅ 部署完成！
echo ========================================
echo.
echo 📱 访问地址: http://localhost:8000
echo 👤 默认账号: admin
echo 🔑 默认密码: admin123
echo.
echo 💡 提示：
echo - 后端服务运行在端口 8001
echo - 前端服务运行在端口 8000
echo - 请保持两个命令行窗口开启
echo - 关闭窗口将停止服务
echo.
pause 