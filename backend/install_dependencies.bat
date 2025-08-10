@echo off
echo ========================================
echo 报价系统依赖安装脚本
echo ========================================
echo.

echo 正在升级pip...
python -m pip install --upgrade pip

echo.
echo 正在安装预编译的numpy...
pip install numpy==1.24.3 --only-binary=all

echo.
echo 正在安装其他依赖...
pip install -r requirements.txt

echo.
echo ========================================
echo 安装完成！
echo ========================================
pause 