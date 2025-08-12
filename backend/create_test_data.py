#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试价格表分页功能的简单脚本
"""

import os
import sys
import pandas as pd

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def create_large_test_price_table():
    """创建一个大的测试价格表来测试分页功能"""
    
    # 创建测试数据
    data = []
    brands = ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '苏州纽威', '永嘉三精']
    product_types = ['截止阀', '球阀', '蝶阀', '闸阀', '止回阀', '调节阀']
    
    for i in range(1, 201):  # 创建200行数据
        brand = brands[i % len(brands)]
        product_type = product_types[i % len(product_types)]
        dn = [25, 32, 40, 50, 65, 80, 100, 125, 150, 200][i % 10]
        
        data.append({
            '产品名称': f'{product_type}',
            '型号': f'MODEL-{i:03d}',
            '规格': f'DN{dn}',
            '单价': round(100 + (i * 15.5) % 2000, 2),
            '品牌': brand,
            '材质': ['不锈钢', '碳钢', '球墨铸铁', '青铜'][i % 4],
            '压力等级': f'PN{[10, 16, 25, 40][i % 4]}',
            '备注': f'测试产品{i}'
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存到测试数据目录
    test_dir = os.path.join(current_dir, 'merchant_data', 'admin', '价格表')
    os.makedirs(test_dir, exist_ok=True)
    
    file_path = os.path.join(test_dir, '大型测试价格表.xlsx')
    df.to_excel(file_path, index=False)
    
    print(f"✅ 创建了包含 {len(data)} 行数据的测试价格表")
    print(f"📄 文件路径: {file_path}")
    print(f"📊 列名: {list(df.columns)}")
    print(f"🏷️ 品牌数量: {df['品牌'].nunique()}")
    
    return file_path

if __name__ == "__main__":
    print("🧪 创建大型测试价格表以测试分页功能")
    print("=" * 50)
    
    try:
        file_path = create_large_test_price_table()
        print("\n🎉 测试价格表创建成功！")
        print("\n📝 接下来可以:")
        print("1. 启动后端服务: python main.py")
        print("2. 访问前端界面测试分页功能")
        print("3. 或运行: python test_pagination.py 进行API测试")
        
    except Exception as e:
        print(f"❌ 创建测试价格表失败: {e}")
        import traceback
        traceback.print_exc()
