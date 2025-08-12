#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试价格表分页功能
"""

import requests
import json
from base64 import b64encode

def test_price_table_pagination():
    base_url = "http://localhost:8000"
    
    # 测试用户凭据 (需要根据实际情况修改)
    username = "test"
    password = "test"
    credentials = b64encode(f"{username}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    
    print("🔍 测试价格表分页功能")
    print("=" * 50)
    
    # 1. 测试获取价格表列表
    print("\n1. 获取价格表列表:")
    try:
        response = requests.get(f"{base_url}/api/price-tables", headers=headers)
        if response.status_code == 200:
            files = response.json()["files"]
            print(f"✅ 成功获取 {len(files)} 个价格表文件")
            for file_info in files:
                print(f"   📄 {file_info['filename']} - {file_info.get('row_count', '?')} 行")
            
            # 如果有文件，测试分页
            if files:
                test_filename = files[0]["filename"]
                print(f"\n2. 测试文件 '{test_filename}' 的分页功能:")
                
                # 测试第一页
                response = requests.get(
                    f"{base_url}/api/price-table/{test_filename}?page=1&page_size=10", 
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    pagination = data["pagination"]
                    print(f"✅ 第1页: {len(data['data'])} 行数据")
                    print(f"   总共 {pagination['total_rows']} 行, {pagination['total_pages']} 页")
                    print(f"   当前页: {pagination['current_page']}")
                    print(f"   每页显示: {pagination['page_size']}")
                    print(f"   显示范围: {pagination['start_index']}-{pagination['end_index']}")
                    print(f"   有下一页: {pagination['has_next']}")
                    print(f"   有上一页: {pagination['has_prev']}")
                    
                    # 如果有多页，测试第二页
                    if pagination['total_pages'] > 1:
                        response = requests.get(
                            f"{base_url}/api/price-table/{test_filename}?page=2&page_size=10", 
                            headers=headers
                        )
                        if response.status_code == 200:
                            data2 = response.json()
                            pagination2 = data2["pagination"]
                            print(f"✅ 第2页: {len(data2['data'])} 行数据")
                            print(f"   显示范围: {pagination2['start_index']}-{pagination2['end_index']}")
                        else:
                            print(f"❌ 获取第2页失败: {response.status_code}")
                    else:
                        print("ℹ️ 只有一页数据")
                else:
                    print(f"❌ 获取价格表内容失败: {response.status_code}")
                    print(response.text)
            else:
                print("ℹ️ 没有找到价格表文件")
        else:
            print(f"❌ 获取价格表列表失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_price_table_pagination()
