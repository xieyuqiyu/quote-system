#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from PIL import Image
import pytesseract

def diagnose_ocr_environment():
    """诊断OCR环境"""
    print("🔍 OCR环境诊断")
    print("=" * 50)
    
    # 1. 检查Python环境
    print("🐍 Python环境:")
    print(f"   Python版本: {sys.version}")
    print(f"   当前目录: {os.getcwd()}")
    
    # 2. 检查pytesseract
    print("\n📦 pytesseract:")
    try:
        print(f"   pytesseract版本: {pytesseract.get_tesseract_version()}")
        print("   ✅ pytesseract可用")
    except Exception as e:
        print(f"   ❌ pytesseract不可用: {e}")
    
    # 3. 检查tesseract可执行文件
    print("\n🔧 Tesseract可执行文件:")
    tesseract_paths = [
        r"D:\图片\tesseract.exe",
        r"D:\tupian\tesseract.exe",
        "tesseract",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract"
    ]
    
    tesseract_found = False
    for path in tesseract_paths:
        try:
            if os.path.exists(path):
                print(f"   ✅ 找到tesseract: {path}")
                # 测试版本
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    print(f"   版本: {version}")
                    tesseract_found = True
                    break
                else:
                    print(f"   ⚠️  无法执行: {path}")
            else:
                print(f"   ❌ 不存在: {path}")
        except Exception as e:
            print(f"   ❌ 检查失败: {path} - {e}")
    
    if not tesseract_found:
        print("   ❌ 未找到可用的tesseract可执行文件")
    
    # 4. 检查tessdata目录
    print("\n📁 tessdata目录:")
    tessdata_paths = [
        r"D:\图片",
        r"D:\tupian\tessdata",
        r"D:\tupian",
        "/usr/share/tessdata",
        "/usr/local/share/tessdata"
    ]
    
    tessdata_found = False
    for path in tessdata_paths:
        if os.path.exists(path):
            print(f"   ✅ 找到tessdata目录: {path}")
            # 检查语言包
            eng_path = os.path.join(path, "eng.traineddata")
            if os.path.exists(eng_path):
                print(f"   ✅ 找到英文语言包: {eng_path}")
                tessdata_found = True
            else:
                print(f"   ⚠️  缺少英文语言包: {eng_path}")
            
            # 列出目录内容
            try:
                files = os.listdir(path)
                trained_files = [f for f in files if f.endswith('.traineddata')]
                print(f"   语言包数量: {len(trained_files)}")
                if trained_files:
                    print(f"   语言包列表: {trained_files[:5]}...")
            except Exception as e:
                print(f"   ❌ 无法读取目录: {e}")
            break
        else:
            print(f"   ❌ 不存在: {path}")
    
    if not tessdata_found:
        print("   ❌ 未找到可用的tessdata目录")
    
    # 5. 测试OCR功能
    print("\n🧪 OCR功能测试:")
    try:
        # 创建一个简单的测试图片
        test_image = Image.new('RGB', (200, 100), color='white')
        
        # 设置tesseract路径
        if tesseract_found:
            pytesseract.pytesseract.tesseract_cmd = path
        else:
            # 使用默认配置
            pytesseract.pytesseract.tesseract_cmd = r"D:\tupian\tesseract.exe"
            os.environ['TESSDATA_PREFIX'] = r'D:\tupian\tessdata'
        
        # 测试OCR
        text = pytesseract.image_to_string(test_image, lang='eng')
        print("   ✅ OCR功能正常")
        print(f"   测试结果: '{text.strip()}'")
        
    except Exception as e:
        print(f"   ❌ OCR功能测试失败: {e}")
    
    # 6. 环境变量检查
    print("\n🌍 环境变量:")
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        print(f"   TESSDATA_PREFIX: {tessdata_prefix}")
        if os.path.exists(tessdata_prefix):
            print("   ✅ TESSDATA_PREFIX路径有效")
        else:
            print("   ❌ TESSDATA_PREFIX路径无效")
    else:
        print("   TESSDATA_PREFIX: 未设置")
    
    # 7. 建议
    print("\n💡 建议:")
    if not tesseract_found:
        print("   1. 安装Tesseract OCR")
        print("   2. 设置正确的tesseract_cmd路径")
    
    if not tessdata_found:
        print("   3. 下载语言包到tessdata目录")
        print("   4. 设置TESSDATA_PREFIX环境变量")
    
    print("\n🔧 当前配置:")
    print(f"   pytesseract.tesseract_cmd: {pytesseract.pytesseract.tesseract_cmd}")
    print(f"   TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', '未设置')}")

if __name__ == "__main__":
    diagnose_ocr_environment() 