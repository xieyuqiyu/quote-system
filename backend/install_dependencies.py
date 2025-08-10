#!/usr/bin/env python3
"""
报价系统依赖安装脚本
解决Windows上numpy编译问题
"""

import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"\n{description}...")
    print(f"执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description}成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败")
        print(f"错误代码: {e.returncode}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def main():
    print("=" * 50)
    print("报价系统依赖安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 8:
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    # 升级pip
    if not run_command("python -m pip install --upgrade pip", "升级pip"):
        print("⚠️ pip升级失败，继续安装...")
    
    # 安装预编译的numpy
    print("\n🔧 尝试安装预编译的numpy...")
    
    # 方法1: 使用--only-binary=all强制使用预编译包
    if run_command("pip install numpy==1.24.3 --only-binary=all", "安装numpy (方法1)"):
        print("✅ numpy安装成功")
    else:
        # 方法2: 尝试安装更老的版本
        print("\n🔧 尝试安装更老的numpy版本...")
        if run_command("pip install numpy==1.23.5 --only-binary=all", "安装numpy (方法2)"):
            print("✅ numpy安装成功")
        else:
            # 方法3: 使用conda-forge
            print("\n🔧 尝试使用conda安装...")
            if run_command("conda install numpy=1.24.3 -c conda-forge -y", "使用conda安装numpy"):
                print("✅ numpy安装成功")
            else:
                print("❌ 所有numpy安装方法都失败了")
                print("请尝试以下解决方案:")
                print("1. 安装Visual Studio Build Tools")
                print("2. 使用Anaconda/Miniconda")
                print("3. 下载预编译的wheel文件手动安装")
                return False
    
    # 安装其他依赖
    print("\n📦 安装其他依赖...")
    if not run_command("pip install -r requirements.txt", "安装其他依赖"):
        print("❌ 其他依赖安装失败")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 所有依赖安装完成！")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 安装过程中出现错误，请检查上述错误信息")
        input("按回车键退出...")
    else:
        print("\n🎉 安装成功！可以启动系统了")
        input("按回车键退出...") 