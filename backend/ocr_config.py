#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
from pathlib import Path

def get_tesseract_path():
    """
    动态检测tesseract路径，支持开发环境和打包环境
    """
    # 1. 优先使用打包的tesseract
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
        if platform.system() == "Windows":
            tesseract_path = os.path.join(base_path, 'tesseract', 'tesseract.exe')
        else:
            tesseract_path = os.path.join(base_path, 'tesseract', 'tesseract')
        
        if os.path.exists(tesseract_path):
            print(f"🔧 [OCR] 使用打包的tesseract: {tesseract_path}")
            return tesseract_path
    
    # 2. 检查环境变量
    env_tesseract = os.environ.get('TESSERACT_CMD')
    if env_tesseract and os.path.exists(env_tesseract):
        print(f"🔧 [OCR] 使用环境变量tesseract: {env_tesseract}")
        return env_tesseract
    
    # 3. 检查系统PATH
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("🔧 [OCR] 使用系统PATH中的tesseract")
            return 'tesseract'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 4. 检查常见安装路径
    common_paths = []
    if platform.system() == "Windows":
        common_paths = [
            r"D:\tupian\tesseract.exe",
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
        ]
    else:
        common_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract"
        ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"🔧 [OCR] 使用常见路径tesseract: {path}")
            return path
    
    # 5. 默认路径（开发环境）
    default_path = r"D:\tupian\tesseract.exe" if platform.system() == "Windows" else "/usr/bin/tesseract"
    print(f"⚠️  [OCR] 使用默认路径tesseract: {default_path}")
    return default_path

def get_tessdata_path():
    """
    动态检测tessdata路径
    """
    # 1. 优先使用打包的tessdata
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        tessdata_path = os.path.join(base_path, 'tessdata')
        if os.path.exists(tessdata_path):
            print(f"🔧 [OCR] 使用打包的tessdata: {tessdata_path}")
            return tessdata_path
    
    # 2. 检查环境变量
    env_tessdata = os.environ.get('TESSDATA_PREFIX')
    if env_tessdata and os.path.exists(env_tessdata):
        print(f"🔧 [OCR] 使用环境变量tessdata: {env_tessdata}")
        return env_tessdata
    
    # 3. 根据tesseract路径推断tessdata路径
    tesseract_path = get_tesseract_path()
    if tesseract_path and os.path.exists(tesseract_path):
        # 尝试推断tessdata路径
        tesseract_dir = os.path.dirname(tesseract_path)
        possible_tessdata_paths = [
            os.path.join(tesseract_dir, 'tessdata'),
            os.path.join(os.path.dirname(tesseract_dir), 'tessdata'),
            os.path.join(tesseract_dir, '..', 'tessdata')
        ]
        
        for path in possible_tessdata_paths:
            if os.path.exists(path):
                print(f"🔧 [OCR] 推断tessdata路径: {path}")
                return path
    
    # 4. 默认路径（开发环境）
    default_path = r"D:\tupian\tessdata" if platform.system() == "Windows" else "/usr/share/tessdata"
    print(f"⚠️  [OCR] 使用默认tessdata路径: {default_path}")
    return default_path

def setup_ocr_environment():
    """
    设置OCR环境，配置pytesseract和tessdata路径
    """
    try:
        import pytesseract
        
        # 设置tesseract路径
        tesseract_path = get_tesseract_path()
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 设置tessdata路径
        tessdata_path = get_tessdata_path()
        os.environ['TESSDATA_PREFIX'] = tessdata_path
        
        print(f"✅ [OCR] 环境配置完成")
        print(f"   tesseract: {tesseract_path}")
        print(f"   tessdata: {tessdata_path}")
        
        # 验证配置
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ [OCR] tesseract版本: {version}")
            return True
        except Exception as e:
            print(f"❌ [OCR] tesseract版本检查失败: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ [OCR] pytesseract导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ [OCR] 环境配置失败: {e}")
        return False

def check_ocr_availability():
    """
    检查OCR功能是否可用
    """
    try:
        import pytesseract
        from PIL import Image
        
        # 创建测试图片
        test_image = Image.new('RGB', (100, 50), color='white')
        
        # 测试OCR
        text = pytesseract.image_to_string(test_image, lang='eng')
        print(f"✅ [OCR] 功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ [OCR] 功能测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 [OCR] 开始配置OCR环境...")
    if setup_ocr_environment():
        print("✅ [OCR] 环境配置成功")
        if check_ocr_availability():
            print("✅ [OCR] 功能测试通过")
        else:
            print("❌ [OCR] 功能测试失败")
    else:
        print("❌ [OCR] 环境配置失败") 