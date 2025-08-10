#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
from pathlib import Path

def test_file_upload():
    """测试文件上传功能"""
    
    # 服务器地址
    base_url = "http://localhost:8001"
    
    # 登录获取认证
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🔐 登录测试...")
    try:
        response = requests.post(f"{base_url}/api/login", auth=("admin", "admin123"))
        if response.status_code == 200:
            print("✅ 登录成功")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 测试文件列表
    test_files = [
        # 图片文件
        "quote-system/9ce048b41c461644f43ceca6dc11ad5d.jpg",
        "quote-system/123.png",
        "quote-system/3 (2)_01.png",
        
        # Word文件
        "quote-system/123.docx",
    ]
    
    # 测试上传
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue
            
        print(f"\n📤 测试上传文件: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                
                # 测试询价表上传
                print(f"  🔄 上传到询价表...")
                response = requests.post(
                    f"{base_url}/api/upload/inquiry",
                    files=files,
                    auth=("admin", "admin123")
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ 询价表上传成功: {result.get('filename', 'N/A')}")
                else:
                    print(f"  ❌ 询价表上传失败: {response.status_code} - {response.text}")
                
                # 如果是图片文件，也测试OCR专用接口
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    print(f"  🔄 测试OCR处理...")
                    f.seek(0)  # 重置文件指针
                    response = requests.post(
                        f"{base_url}/api/ocr/process-image",
                        files=files,
                        auth=("admin", "admin123")
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ OCR处理成功:")
                        print(f"     原始文本长度: {len(result.get('original_text', ''))}")
                        print(f"     提取项目数: {result.get('statistics', {}).get('extracted_items', 0)}")
                    else:
                        print(f"  ❌ OCR处理失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ 上传异常: {e}")
    
    print("\n📋 获取文件列表...")
    try:
        response = requests.get(f"{base_url}/api/files", auth=("admin", "admin123"))
        if response.status_code == 200:
            files = response.json()
            print("✅ 文件列表获取成功:")
            print(f"   价格表: {len(files.get('price_tables', []))} 个")
            print(f"   询价表: {len(files.get('inquiry_tables', []))} 个")
            print(f"   报价单: {len(files.get('quotes', []))} 个")
            
            # 显示最新的询价表文件
            inquiry_files = files.get('inquiry_tables', [])
            if inquiry_files:
                print(f"   最新询价表: {inquiry_files[0]}")
        else:
            print(f"❌ 获取文件列表失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 获取文件列表异常: {e}")

if __name__ == "__main__":
    test_file_upload() 