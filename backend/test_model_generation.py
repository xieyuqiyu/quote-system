#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试标准型号生成功能 - 模拟合并所有单元格信息
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from valve_model_generator import parse_valve_info_from_combined
from csv_utils import safe_read_csv

def test_combined_cell_model_generation():
    """测试合并所有单元格信息的标准型号生成"""
    print("🧪 测试合并所有单元格信息的标准型号生成功能")
    print("=" * 80)
    
    # 模拟询价表数据 - 每行包含多个单元格的信息，包括数量、单位等所有信息
    test_data = [
        {
            "name": "测试1: 基本闸阀 - 所有单元格信息",
            "cells": ["闸阀", "DN50", "PN16", "法兰连接", "10", "个", "铸铁"],
            "expected": "Z41X-16Q"
        },
        {
            "name": "测试2: 不锈钢球阀 - 所有单元格信息",
            "cells": ["球阀", "不锈钢304", "DN25", "PN16", "丝口", "5", "个", "备注信息"],
            "expected": "Q11F-16P"
        },
        {
            "name": "测试3: 电动蝶阀 - 所有单元格信息",
            "cells": ["蝶阀", "电动", "DN100", "PN16", "对夹式", "2", "台", "特殊要求"],
            "expected": "D971X-16Q"
        },
        {
            "name": "测试4: 黄铜球阀 - 所有单元格信息",
            "cells": ["球阀", "黄铜", "DN20", "PN16", "3", "个", "黄铜材质", "丝扣连接"],
            "expected": "Q11F-16T"
        },
        {
            "name": "测试5: 气动闸阀 - 所有单元格信息",
            "cells": ["闸阀", "气动", "DN80", "PN16", "法兰", "1", "套", "气动执行器", "配套"],
            "expected": "Z641X-16Q"
        },
        {
            "name": "测试6: 复杂信息 - 止回阀所有单元格",
            "cells": ["止回阀", "旋启式", "DN65", "PN16", "铸钢", "4", "个", "H44H", "标准"],
            "expected": "H44H-16C"
        }
    ]
    
    print("🔍 测试合并所有单元格信息生成标准型号:")
    
    for i, case in enumerate(test_data, 1):
        print(f"\n--- {case['name']} ---")
        
        # 模拟合并所有单元格信息
        combined_info = ' '.join(case['cells'])
        print(f"所有单元格信息: {case['cells']}")
        print(f"合并后信息: {combined_info}")
        
        # 生成标准型号
        result = parse_valve_info_from_combined(combined_info)
        print(f"生成的标准型号: {result}")
        print(f"期望的标准型号: {case['expected']}")
        
        if result == case['expected']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
    
    print("\n" + "=" * 80)
    print("🔍 测试实际CSV文件处理:")
    
    # 创建一个模拟的CSV数据 - 包括备注等所有列
    sample_data = {
        '品名': ['闸阀', '球阀', '蝶阀'],
        '规格型号': ['DN50', 'DN25 不锈钢', 'DN100'],
        '压力等级': ['PN16', 'PN16', 'PN16'],
        '连接方式': ['法兰', '丝口', '对夹'],
        '材质': ['铸铁', '304不锈钢', '铸铁'],
        '数量': [10, 5, 2],
        '单位': ['个', '个', '个'],
        '备注': ['法兰连接标准', '进口材质', '电动执行器'],
        '特殊要求': ['防腐处理', '高温型', '快速关闭'],
        '供应商': ['厂家A', '厂家B', '厂家C']
    }
    
    df = pd.DataFrame(sample_data)
    print("模拟询价表数据:")
    print(df.to_string(index=False))
    
    print("\n处理每行数据 - 合并所有单元格:")
    
    for index, row in df.iterrows():
        print(f"\n--- 第{index+1}行 ---")
        
        # 合并所有单元格信息 - 真正的所有单元格
        all_cell_info = []
        print(f"所有列信息:")
        for col in df.columns:
            cell_value = row[col]
            print(f"   列'{col}': {cell_value}")
            if pd.notna(cell_value) and str(cell_value).strip():
                cell_str = str(cell_value).strip()
                if cell_str not in all_cell_info:
                    all_cell_info.append(cell_str)
                    print(f"   ✅ 添加到合并信息: {cell_str}")
                else:
                    print(f"   ⚪ 跳过重复信息: {cell_str}")
        
        combined_info = ' '.join(all_cell_info)
        print(f"合并的所有单元格信息: {all_cell_info}")
        print(f"合并后的完整信息: {combined_info}")
        
        # 生成标准型号
        model = parse_valve_info_from_combined(combined_info)
        print(f"生成的标准型号: {model}")
    
    print("\n" + "=" * 80)
    print("测试完成")

if __name__ == "__main__":
    test_combined_cell_model_generation()