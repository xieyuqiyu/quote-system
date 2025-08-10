#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整的单元格合并器 - 确保识别所有单元格，包括备注等所有列
"""

import pandas as pd
import re

def merge_all_cells_complete(row, columns, row_index):
    """
    完整版单元格合并器 - 绝对确保识别所有单元格，包括备注之类的列
    
    Args:
        row: pandas Series - 当前行数据
        columns: list - 所有列名
        row_index: int - 行索引
    
    Returns:
        str: 合并后的完整信息字符串
    """
    print(f"\n{'='*120}")
    print(f"🔍 [COMPLETE-MERGER] 处理第{row_index+1}行 - 绝对识别所有单元格（包括备注等）")
    print(f"{'='*120}")
    
    # 初始化
    all_cell_info = []
    processed_cells = []
    
    print(f"📊 [INFO] 总列数: {len(columns)}")
    print(f"📊 [INFO] 所有列名: {list(columns)}")
    
    # 第一阶段：强制扫描每个单元格
    print(f"\n🔍 [PHASE-1] 强制扫描每个单元格:")
    
    for col_index, col in enumerate(columns):
        cell_value = row[col] if col in row.index else None
        
        print(f"\n   📱 单元格[{col_index+1:02d}] 列名: '{col}'")
        print(f"      原始值: {repr(cell_value)}")
        print(f"      数据类型: {type(cell_value).__name__}")
        
        # 强制处理每种可能的数据类型
        processed_value = None
        processing_note = ""
        
        if pd.notna(cell_value):
            if isinstance(cell_value, str):
                # 字符串类型
                cleaned = cell_value.strip()
                if cleaned:
                    processed_value = cleaned
                    processing_note = "字符串处理"
            elif isinstance(cell_value, (int, float)):
                # 数字类型
                if not (isinstance(cell_value, float) and (pd.isna(cell_value) or cell_value != cell_value)):
                    processed_value = str(cell_value).strip()
                    processing_note = "数字转字符串"
            elif hasattr(cell_value, 'strftime'):
                # 日期时间类型
                try:
                    processed_value = cell_value.strftime('%Y-%m-%d')
                    processing_note = "日期格式化"
                except:
                    processed_value = str(cell_value).strip()
                    processing_note = "日期强制转换"
            elif isinstance(cell_value, bool):
                # 布尔类型
                processed_value = "是" if cell_value else "否"
                processing_note = "布尔值转换"
            else:
                # 其他未知类型
                try:
                    processed_value = str(cell_value).strip()
                    processing_note = "未知类型强制转换"
                except:
                    processed_value = None
                    processing_note = "转换失败"
        else:
            processing_note = "空值跳过"
        
        # 记录处理结果
        if processed_value and processed_value not in ['', 'nan', 'None', 'NaN']:
            processed_cells.append({
                'column': col,
                'index': col_index,
                'original': cell_value,
                'processed': processed_value,
                'type': type(cell_value).__name__,
                'note': processing_note
            })
            
            # 添加到合并列表（去重但保留顺序）
            if processed_value not in all_cell_info:
                all_cell_info.append(processed_value)
                print(f"      ✅ 成功添加: '{processed_value}' ({processing_note})")
            else:
                print(f"      🔄 重复内容: '{processed_value}' ({processing_note})")
        else:
            print(f"      ⚫ 跳过: {processing_note}")
    
    # 第二阶段：特别检查备注相关列
    print(f"\n🔍 [PHASE-2] 特别检查备注相关列:")
    
    remark_keywords = [
        # 中文备注关键词
        '备注', '说明', '注释', '要求', '特殊要求', '技术要求', '补充说明',
        '描述', '详情', '细节', '附加信息', '其他', '补充', '特别说明',
        '注意事项', '使用说明', '安装要求', '维护说明', '操作说明',
        
        # 英文备注关键词
        'remark', 'note', 'comment', 'description', 'memo', 'remarks',
        'notes', 'comments', 'spec', 'specification', 'detail', 'details',
        'requirement', 'requirements', 'instruction', 'instructions'
    ]
    
    remark_found = 0
    for keyword in remark_keywords:
        for col in columns:
            col_lower = str(col).lower()
            if keyword.lower() in col_lower:
                cell_value = row[col] if col in row.index else None
                if pd.notna(cell_value):
                    remark_str = str(cell_value).strip()
                    if remark_str and remark_str not in ['', 'nan', 'None', 'NaN']:
                        if remark_str not in all_cell_info:
                            all_cell_info.append(remark_str)
                            remark_found += 1
                            print(f"   🎯 发现备注信息: '{remark_str}' (来自列: {col})")
                        else:
                            print(f"   🎯 备注信息重复: '{remark_str}' (来自列: {col})")
    
    print(f"   📊 备注信息发现: {remark_found}个")
    
    # 第三阶段：检查可能遗漏的数值和特殊信息
    print(f"\n🔍 [PHASE-3] 检查可能遗漏的信息:")
    
    additional_found = 0
    for col in columns:
        # 检查是否已经处理过这一列
        already_processed = any(cell['column'] == col for cell in processed_cells)
        
        if not already_processed:
            cell_value = row[col] if col in row.index else None
            if pd.notna(cell_value):
                # 尝试提取任何有用信息
                cell_str = str(cell_value).strip()
                if cell_str and cell_str not in ['', 'nan', 'None', 'NaN']:
                    if cell_str not in all_cell_info:
                        all_cell_info.append(cell_str)
                        additional_found += 1
                        print(f"   🔍 发现遗漏信息: '{cell_str}' (来自列: {col})")
    
    print(f"   📊 遗漏信息发现: {additional_found}个")
    
    # 第四阶段：特别处理可能包含多个信息的单元格
    print(f"\n🔍 [PHASE-4] 特别处理复合信息单元格:")
    
    compound_found = 0
    for cell in processed_cells:
        value = cell['processed']
        
        # 检查是否包含分隔符，可能是复合信息
        separators = ['、', '，', ',', ';', '；', '|', '/', '\\', '-', '_']
        for sep in separators:
            if sep in value and len(value.split(sep)) > 1:
                parts = [part.strip() for part in value.split(sep) if part.strip()]
                for part in parts:
                    if part not in all_cell_info and len(part) > 0:
                        all_cell_info.append(part)
                        compound_found += 1
                        print(f"   🔗 发现复合信息: '{part}' (从 '{value}' 分离)")
                break
    
    print(f"   📊 复合信息发现: {compound_found}个")
    
    # 生成最终合并信息
    combined_info = ' '.join(all_cell_info)
    
    # 最终统计
    print(f"\n📊 [FINAL-STATS] 第{row_index+1}行最终统计:")
    print(f"   📊 总列数: {len(columns)}")
    print(f"   📊 处理的单元格: {len(processed_cells)}")
    print(f"   📊 备注信息: {remark_found}")
    print(f"   📊 遗漏信息: {additional_found}")
    print(f"   📊 复合信息: {compound_found}")
    print(f"   📊 最终信息数: {len(all_cell_info)}")
    print(f"   📊 合并长度: {len(combined_info)}字符")
    
    print(f"\n📋 [ALL-INFO] 所有识别到的信息:")
    for i, info in enumerate(all_cell_info, 1):
        print(f"   {i:02d}. '{info}'")
    
    print(f"\n🔧 [FINAL-RESULT] 最终合并信息:")
    print(f"   '{combined_info}'")
    
    print(f"\n📝 [PROCESSING-DETAILS] 详细处理记录:")
    for i, cell in enumerate(processed_cells, 1):
        print(f"   {i:02d}. 列'{cell['column']}' -> '{cell['processed']}' "
              f"({cell['note']}, 原始类型: {cell['type']})")
    
    print(f"{'='*120}")
    
    return combined_info

def test_complete_merger():
    """测试完整的单元格合并器"""
    print("🧪 测试完整的单元格合并器")
    
    # 创建包含各种类型数据的测试数据
    test_data = {
        '品名': '闸阀',
        '规格型号': 'DN50',
        '压力等级': 'PN16',
        '连接方式': '法兰',
        '材质': '铸铁',
        '数量': 10,
        '单位': '个',
        '备注': '特殊要求：防腐处理、高温型',
        '技术要求': '符合国标GB/T12234',
        '供应商': '厂家A',
        '价格': 150.5,
        '交货期': '30天',
        '安装说明': '垂直安装，注意流向',
        '维护要求': '定期检查密封面',
        '其他': '包装要求：木箱包装'
    }
    
    df = pd.DataFrame([test_data])
    row = df.iloc[0]
    columns = df.columns
    
    result = merge_all_cells_complete(row, columns, 0)
    
    print(f"\n🎉 测试完成!")
    print(f"最终合并结果: {result}")
    print(f"信息长度: {len(result)}字符")

if __name__ == "__main__":
    test_complete_merger()