#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """检查打包依赖"""
    print("🔍 检查打包依赖...")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller安装完成")
    
    # 检查其他依赖
    dependencies = [
        'fastapi',
        'uvicorn',
        'pandas',
        'openpyxl',
        'python-docx',
        'pdfplumber',
        'pytesseract',
        'PIL'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装，正在安装...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ {dep} 安装完成")

def check_ocr_environment():
    """检查OCR环境"""
    print("\n🔍 检查OCR环境...")
    
    # 检查tesseract路径
    tesseract_path = r"D:\tupian\tesseract.exe"
    if os.path.exists(tesseract_path):
        print(f"✅ tesseract.exe存在: {tesseract_path}")
    else:
        print(f"❌ tesseract.exe不存在: {tesseract_path}")
        return False
    
    # 检查tessdata路径
    tessdata_path = r"D:\tupian\tessdata"
    if os.path.exists(tessdata_path):
        tessdata_files = [f for f in os.listdir(tessdata_path) if f.endswith('.traineddata')]
        print(f"✅ tessdata目录存在，包含 {len(tessdata_files)} 个训练文件")
    else:
        print(f"❌ tessdata目录不存在: {tessdata_path}")
        return False
    
    return True

def clean_build_directory():
    """清理构建目录"""
    print("\n🧹 清理构建目录...")
    
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ 删除目录: {dir_name}")
    
    # 删除spec文件
    spec_file = 'build_config.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"✅ 删除文件: {spec_file}")

def run_packaging():
    """执行打包"""
    print("\n📦 开始打包...")
    
    try:
        # 使用PyInstaller打包
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "build_config.spec"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 打包成功!")
            return True
        else:
            print(f"❌ 打包失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 打包超时")
        return False
    except Exception as e:
        print(f"❌ 打包异常: {e}")
        return False

def verify_package():
    """验证打包结果"""
    print("\n🔍 验证打包结果...")
    
    dist_dir = "dist/quote_system"
    if not os.path.exists(dist_dir):
        print(f"❌ 打包目录不存在: {dist_dir}")
        return False
    
    # 检查关键文件
    key_files = [
        'quote_system.exe',
        'tesseract/tesseract.exe',
        'tessdata/chi_sim.traineddata',
        'tessdata/eng.traineddata'
    ]
    
    for file_path in key_files:
        full_path = os.path.join(dist_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            return False
    
    # 检查目录大小
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(dist_dir)
        for filename in filenames
    )
    
    print(f"✅ 打包完成，总大小: {total_size / (1024*1024):.1f} MB")
    return True

def main():
    """主函数"""
    print("🚀 开始完整打包流程")
    print("=" * 50)
    
    # 1. 检查依赖
    check_dependencies()
    
    # 2. 检查OCR环境
    if not check_ocr_environment():
        print("❌ OCR环境检查失败，请确保tesseract和tessdata正确安装")
        return False
    
    # 3. 清理构建目录
    clean_build_directory()
    
    # 4. 执行打包
    if not run_packaging():
        print("❌ 打包失败")
        return False
    
    # 5. 验证打包结果
    if not verify_package():
        print("❌ 打包验证失败")
        return False
    
    print("\n🎉 打包完成!")
    print("📁 打包文件位置: dist/quote_system/")
    print("🚀 运行方式: dist/quote_system/quote_system.exe")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 