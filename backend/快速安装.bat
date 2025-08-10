@echo off
chcp 65001
echo ========================================
echo 报价系统快速安装脚本
echo ========================================
echo.

echo 正在清理临时文件...
rmdir /s /q "%TEMP%\pip-*" 2>nul

echo.
echo 正在升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo 正在安装numpy (使用清华镜像源)...
pip install numpy==1.23.5 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --only-binary=all

echo.
echo 正在安装其他依赖...
pip install -r requirements_simple.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo ========================================
echo 安装完成！
echo ========================================
pause 