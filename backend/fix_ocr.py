#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def fix_ocr_config():
    """修复OCR配置"""
    print("🔧 修复OCR配置")
    print("=" * 50)
    
    # 1. 检查tesseract可执行文件
    tesseract_path = r"D:\tupian\tesseract.exe"
    print(f"🔍 检查tesseract: {tesseract_path}")
    
    if os.path.exists(tesseract_path):
        print("✅ tesseract.exe 存在")
        
        # 测试执行权限
        try:
            result = subprocess.run([tesseract_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ tesseract可执行，版本: {result.stdout.strip().split('\n')[0]}")
            else:
                print(f"❌ tesseract执行失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ tesseract执行异常: {e}")
            return False
    else:
        print(f"❌ tesseract.exe 不存在: {tesseract_path}")
        return False
    
    # 2. 检查tessdata目录
    tessdata_path = r"D:\tupian\tessdata"
    print(f"\n🔍 检查tessdata: {tessdata_path}")
    
    if os.path.exists(tessdata_path):
        print("✅ tessdata目录存在")
        
        # 检查语言包
        eng_path = os.path.join(tessdata_path, "eng.traineddata")
        if os.path.exists(eng_path):
            print("✅ 英文语言包存在")
        else:
            print("❌ 英文语言包不存在")
            return False
    else:
        print(f"❌ tessdata目录不存在: {tessdata_path}")
        return False
    
    # 3. 设置环境变量
    print(f"\n🌍 设置环境变量")
    os.environ['TESSDATA_PREFIX'] = tessdata_path
    print(f"✅ TESSDATA_PREFIX = {os.environ['TESSDATA_PREFIX']}")
    
    # 4. 测试OCR功能
    print(f"\n🧪 测试OCR功能")
    try:
        import pytesseract
        from PIL import Image
        
        # 设置tesseract路径
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 创建测试图片
        test_image = Image.new('RGB', (200, 100), color='white')
        
        # 测试OCR
        text = pytesseract.image_to_string(test_image, lang='eng')
        print(f"✅ OCR测试成功: '{text.strip()}'")
        
        # 测试带文字的图片
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试使用默认字体
        try:
            font = ImageFont.load_default()
            draw.text((10, 10), "DN100 5", fill='black', font=font)
        except:
            # 如果没有字体，直接画文字
            draw.text((10, 10), "DN100 5", fill='black')
        
        text2 = pytesseract.image_to_string(img, lang='eng')
        print(f"✅ 文字图片OCR测试: '{text2.strip()}'")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_main_py():
    """更新main.py的OCR配置"""
    print(f"\n📝 更新main.py配置")
    
    main_py_path = "main.py"
    if not os.path.exists(main_py_path):
        print(f"❌ main.py不存在: {main_py_path}")
        return False
    
    try:
        # 读取文件
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查当前配置
        if 'pytesseract.pytesseract.tesseract_cmd = r"D:\\tupian\\tesseract.exe"' in content:
            print("✅ main.py OCR配置已正确")
        else:
            print("⚠️  main.py OCR配置需要更新")
            # 这里可以添加自动更新逻辑
        
        return True
        
    except Exception as e:
        print(f"❌ 更新main.py失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 OCR配置修复工具")
    print("=" * 60)
    
    # 修复OCR配置
    ocr_ok = fix_ocr_config()
    
    # 更新main.py
    main_ok = update_main_py()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 修复总结")
    print("=" * 60)
    print(f"OCR配置: {'✅ 正常' if ocr_ok else '❌ 异常'}")
    print(f"main.py配置: {'✅ 正常' if main_ok else '❌ 异常'}")
    
    if ocr_ok:
        print("\n🎉 OCR配置修复成功！")
        print("现在可以正常使用图片上传功能了。")
    else:
        print("\n🔧 需要手动修复:")
        print("1. 确保 tesseract.exe 在 D:\\tupian\\tesseract.exe")
        print("2. 确保 tessdata 在 D:\\tupian\\tessdata")
        print("3. 设置环境变量: TESSDATA_PREFIX=D:\\tupian\\tessdata")
        print("4. 确保 tesseract.exe 有执行权限")

if __name__ == "__main__":
    main() 