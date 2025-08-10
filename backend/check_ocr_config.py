#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback

# 添加tesseract.exe路径
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'D:\tupian\tesseract.exe'  # 请根据实际路径修改
except ImportError:
    pass

def check_ocr_config():
    print("=== OCR配置检查 ===")
    
    # 1. 检查pytesseract导入
    try:
        import pytesseract
        print("✓ pytesseract模块导入成功")
    except ImportError as e:
        print(f"✗ pytesseract模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ pytesseract模块导入异常: {e}")
        traceback.print_exc()
        return False
    
    # 2. 检查pytesseract版本
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ pytesseract版本: {version}")
    except Exception as e:
        print(f"✗ pytesseract版本检查失败: {e}")
        traceback.print_exc()
        return False
    
    # 3. 检查tesseract_cmd配置
    try:
        tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
        print(f"✓ tesseract_cmd: {tesseract_cmd}")
        
        # 检查文件是否存在
        if os.path.exists(tesseract_cmd):
            print(f"✓ tesseract.exe文件存在")
        else:
            print(f"✗ tesseract.exe文件不存在: {tesseract_cmd}")
            return False
    except Exception as e:
        print(f"✗ tesseract_cmd检查失败: {e}")
        traceback.print_exc()
        return False
    
    # 4. 检查环境变量
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        print(f"✓ TESSDATA_PREFIX: {tessdata_prefix}")
        if os.path.exists(tessdata_prefix):
            print(f"✓ tessdata目录存在")
        else:
            print(f"✗ tessdata目录不存在: {tessdata_prefix}")
            return False
    else:
        print("✗ TESSDATA_PREFIX环境变量未设置")
        return False
    
    # 5. 检查tessdata目录内容
    try:
        tessdata_files = os.listdir(tessdata_prefix)
        chi_sim_files = [f for f in tessdata_files if f.startswith('chi_sim')]
        eng_files = [f for f in tessdata_files if f.startswith('eng')]
        print(f"✓ tessdata目录包含 {len(tessdata_files)} 个文件")
        print(f"✓ 中文训练文件: {len(chi_sim_files)} 个")
        print(f"✓ 英文训练文件: {len(eng_files)} 个")
        
        # 显示前几个文件
        print(f"✓ tessdata文件列表: {tessdata_files[:5]}...")
    except Exception as e:
        print(f"✗ tessdata目录检查失败: {e}")
        traceback.print_exc()
        return False
    
    # 6. 检查PIL导入
    try:
        from PIL import Image
        print("✓ PIL模块导入成功")
    except ImportError as e:
        print(f"✗ PIL模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ PIL模块导入异常: {e}")
        traceback.print_exc()
        return False
    
    # 7. 测试OCR功能
    print("\n=== OCR功能测试 ===")
    
    # 创建测试图片
    try:
        test_image = create_test_image()
        test_image_path = "test_ocr.png"
        test_image.save(test_image_path)
        print("✓ 测试图片创建成功")
    except Exception as e:
        print(f"✗ 测试图片创建失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        # 测试英文OCR
        text_en = pytesseract.image_to_string(test_image, lang='eng')
        print(f"✓ 英文OCR测试成功: '{text_en.strip()}'")
        
        # 测试中文OCR
        text_chi = pytesseract.image_to_string(test_image, lang='chi_sim')
        print(f"✓ 中文OCR测试成功: '{text_chi.strip()}'")
        
        # 测试混合语言OCR
        text_mixed = pytesseract.image_to_string(test_image, lang='eng+chi_sim')
        print(f"✓ 混合语言OCR测试成功: '{text_mixed.strip()}'")
        
    except Exception as e:
        print(f"✗ OCR功能测试失败: {e}")
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print("✓ 测试文件清理完成")
    
    print("\n=== 配置检查完成 ===")
    return True

def create_test_image():
    """创建一个包含测试文字的图片"""
    from PIL import Image
    # 创建一个白色背景的图片
    img = Image.new('RGB', (400, 200), color='white')
    
    # 这里我们创建一个简单的测试图片
    # 实际测试中，您可以使用真实的图片文件
    return img

if __name__ == "__main__":
    try:
        success = check_ocr_config()
        if success:
            print("✓ 所有检查通过！OCR配置正确。")
            sys.exit(0)
        else:
            print("✗ 配置检查失败，请检查上述错误。")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 脚本执行异常: {e}")
        traceback.print_exc()
        sys.exit(1) 