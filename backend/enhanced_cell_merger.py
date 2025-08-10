#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的单元格合并器 - 确保识别所有单元格，包括备注等所有列
"""

import pandas as pd
import re

def merge_all_cells_enhanced(row, columns, row_index):
    """
    增强版单元格合并器 - 确保识别所有单元格，包括备注之类的列
    
    Args:
        row: pandas Series - 当前行数据
        columns: list - 所有列名
        row_index: int - 行索引
    
    Returns:
        dict: 包含合并信息和详细统计的字典
    """
    print(f"\n{'='*100}")
    print(f"🔍 [ENHANCED-MERGER] 处理第{row_index+1}行 - 强制识别所有单元格")
    print(f"{'='*100}")
    
    # 初始化结果
    all_cell_info = []
    cell_details = []
    processed_count = 0
    skipped_count = 0
    
    print(f"📊 [STATS] 总列数: {len(columns)}")
    print(f"📊 [STATS] 列名列表: {list(columns)}")
    
    # 第一轮：逐个扫描所有单元格
    print(f"\n🔍 [PHASE-1] 第一轮扫描 - 逐个检查所有单元格:")
    
    for col_index, col in enumerate(columns):
        cell_value = row[col] if col in row.index else None
        cell_type = type(cell_value).__name__
        
        print(f"   📱 [{col_index+1:02d}] 列:'{col}' | 值:{repr(cell_value)} | 类型:{cell_type}")
        
        # 强制处理所有可能的数据类型
        cell_str = None
        processing_method = "未处理"
        
        if pd.notna(cell_value):
            if isinstance(cell_value, (int, float)):
                # 数字类型处理
                if not (isinstance(cell_value, float) and (pd.isna(cell_value) or cell_value != cell_value)):
                    cell_str = str(cell_value).strip()
                    processing_method = "数字转换"
            elif isinstance(cell_value, str):
                # 字符串类型处理
                cell_str = cell_value.strip()
                processing_method = "字符串清理"
            elif hasattr(cell_value, 'strftime'):
                # 日期时间类型处理
                try:
                    cell_str = cell_value.strftime('%Y-%m-%d %H:%M:%S')
                    processing_method = "日期格式化"
                except:
                    cell_str = str(cell_value).strip()
                    processing_method = "日期转字符串"
            elif isinstance(cell_value, bool):
                # 布尔类型处理
                cell_str = "是" if cell_value else "否"
                processing_method = "布尔转换"
            else:
                # 其他类型强制转换
                try:
                    cell_str = str(cell_value).strip()
                    processing_method = "强制转换"
                except:
                    cell_str = None
                    processing_method = "转换失败"
        
        # 验证处理结果
        if cell_str and cell_str not in ['', 'nan', 'None', 'NaN']:
            # 记录详细信息
            detail = {
                'column': col,
                'column_index': col_index,
                'original_value': cell_value,
                'processed_value': cell_str,
                'original_type': cell_type,
                'processing_method': processing_method,
                'length': len(cell_str)
            }
            cell_details.append(detail)
            
            # 添加到合并列表（允许重复，因为不同列可能有不同含义）
            if cell_str not in all_cell_info:
                all_cell_info.append(cell_str)
                processed_count += 1
                print(f"   ✅ 成功处理: '{cell_str}' ({processing_method})")
            else:
                print(f"   🔄 重复内容: '{cell_str}' ({processing_method}) - 已存在但记录来源")
        else:
            skipped_count += 1
            print(f"   ⚫ 跳过: {processing_method}")
    
    # 第二轮：特别检查备注相关列
    print(f"\n🔍 [PHASE-2] 第二轮扫描 - 特别检查备注相关列:")
    
    remark_keywords = [
        '备注', '说明', '注释', '要求', '特殊要求', '技术要求', '补充说明',
        'remark', 'note', 'comment', 'description', 'memo', 'remarks',
        '描述', '详情', '细节', '附加信息', '其他', '补充', '特别说明'
    ]
    
    remark_found = 0
    for keyword in remark_keywords:
        for col in columns:
            col_lower = str(col).lower()
            if keyword.lower() in col_lower:
                cell_value = row[col] if col in row.index else None
                if pd.notna(cell_value) and str(cell_value).strip():
                    remark_str = str(cell_value).strip()
                    if remark_str not in all_cell_info and remark_str not in ['', 'nan', 'None']:
                        all_cell_info.append(remark_str)
                        remark_found += 1
                        print(f"   🎯 发现备注: '{remark_str}' (来自列: {col})")
                        
                        # 补充到详细信息
                        cell_details.append({
                            'column': col,
                            'column_index': list(columns).index(col),
                            'original_value': cell_value,
                            'processed_value': remark_str,
                            'original_type': type(cell_value).__name__,
                            'processing_method': '备注特别处理',
                            'length': len(remark_str)
                        })
    
    print(f"   📊 备注相关信息发现: {remark_found}个")
    
    # 第三轮：检查可能被忽略的数值列
    print(f"\n🔍 [PHASE-3] 第三轮扫描 - 检查数值和特殊列:")
    
    numeric_found = 0
    for col in columns:
        if col not in [detail['column'] for detail in cell_details]:
            cell_value = row[col] if col in row.index else None
            if pd.notna(cell_value):
                # 特别处理可能被忽略的数值
                if isinstance(cell_value, (int, float)) and cell_value != 0:
                    cell_str = str(cell_value)
                    if cell_str not in all_cell_info:
                        all_cell_info.append(cell_str)
                        numeric_found += 1
                        print(f"   🔢 发现数值: '{cell_str}' (来自列: {col})")
    
    print(f"   📊 数值信息发现: {numeric_found}个")
    
    # 生成最终合并信息
    combined_info = ' '.join(all_cell_info)
    
    # 详细统计
    print(f"\n📊 [FINAL-STATS] 第{row_index+1}行处理统计:")
    print(f"   📊 总列数: {len(columns)}")
    print(f"   📊 处理成功: {processed_count}个")
    print(f"   📊 跳过空值: {skipped_count}个")
    print(f"   📊 备注发现: {remark_found}个")
    print(f"   📊 数值发现: {numeric_found}个")
    print(f"   📊 最终信息数: {len(all_cell_info)}个")
    print(f"   📊 合并长度: {len(combined_info)}字符")
    
    print(f"\n📋 [CELL-LIST] 所有识别到的信息:")
    for i, info in enumerate(all_cell_info, 1):
        print(f"   {i:02d}. '{info}'")
    
    print(f"\n🔧 [COMBINED] 最终合并信息:")
    print(f"   '{combined_info}'")
    
    print(f"\n📝 [DETAILS] 详细处理记录:")
    for i, detail in enumerate(cell_details, 1):
        print(f"   {i:02d}. 列'{detail['column']}' -> '{detail['processed_value']}' "
              f"({detail['processing_method']}, {detail['length']}字符)")
    
    return {
        'combined_info': combined_info,
        'all_cell_info': all_cell_info,
        'cell_details': cell_details,
        'stats': {
            'total_columns': len(columns),
            'processed_count': processed_count,
            'skipped_count': skipped_count,
            'remark_found': remark_found,
            'numeric_found': numeric_found,
            'final_info_count': len(all_cell_info),
            'combined_length': len(combined_info)
        }
    }

def test_enhanced_merger():
    """测试增强的单元格合并器"""
    print("🧪 测试增强的单元格合并器")
    
    # 创建测试数据
    test_data = {
        '品名': '闸阀',
        '规格型号': 'DN50',
        '压力等级': 'PN16',
        '连接方式': '法兰',
        '材质': '铸铁',
        '数量': 10,
        '单位': '个',
        '备注': '特殊要求：防腐处理',
        '技术要求': '高温型',
        '供应商': '厂家A',
        '价格': 150.5,
        '交货期': '30天'
    }
    
    df = pd.DataFrame([test_data])
    row = df.iloc[0]
    columns = df.columns
    
    result = merge_all_cells_enhanced(row, columns, 0)
    
    print(f"\n🎉 测试完成!")
    print(f"合并结果: {result['combined_info']}")
    print(f"信息数量: {result['stats']['final_info_count']}")

if __name__ == "__main__":
    test_enhanced_merger()