#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新的报价生成流程 - 按照要求的顺序：最后生成标准型号，然后匹配价格
"""

import os
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime
from csv_utils import safe_read_csv, safe_to_csv
from valve_model_generator import parse_valve_info_from_combined
from generate_quotes import process_inquiry_file

def generate_quote_with_new_order(inquiry_path, price_path, output_dir, username, company):
    """
    按照新顺序生成报价：
    1. 处理询价表
    2. 准备价格表
    3. 最后生成标准型号（合并所有单元格）
    4. 基于标准型号匹配价格
    """
    print("🚀 [NEW-QUOTE] 开始新顺序的报价生成流程")
    print(f"📁 [NEW-QUOTE] 询价文件: {inquiry_path}")
    print(f"💰 [NEW-QUOTE] 价格文件: {price_path}")
    print(f"👤 [NEW-QUOTE] 用户: {username}")
    print(f"🏢 [NEW-QUOTE] 公司: {company}")
    
    try:
        # 步骤1: 处理询价表为标准格式
        print("📊 [NEW-QUOTE] 步骤1: 处理询价表...")
        
        if inquiry_path.endswith(('.xlsx', '.xls')):
            from convert_excel_to_csv import process_excel_to_standard_csv
            standard_csv = os.path.join(output_dir, "standard_inquiry.csv")
            process_excel_to_standard_csv(inquiry_path, standard_csv)
        else:
            # CSV文件直接复制
            standard_csv = os.path.join(output_dir, "standard_inquiry.csv")
            shutil.copy2(inquiry_path, standard_csv)
        
        # 读取标准化的询价表
        df = safe_read_csv(standard_csv)
        print(f"📋 [NEW-QUOTE] 询价表读取完成，共{len(df)}行")
        
        # 步骤2: 准备价格表数据
        print("💰 [NEW-QUOTE] 步骤2: 准备价格表数据...")
        
        # 读取价格表
        if price_path.endswith('.csv'):
            price_df = safe_read_csv(price_path)
        else:
            price_df = pd.read_excel(price_path)
        
        # 标准化价格表列名
        column_mapping = {}
        for col in price_df.columns:
            col_lower = str(col).lower()
            if '型号' in col_lower:
                column_mapping[col] = '型号'
            elif '规格' in col_lower or 'dn' in col_lower:
                column_mapping[col] = '规格'
            elif '品牌' in col_lower:
                column_mapping[col] = '品牌'
            elif '价格' in col_lower or '单价' in col_lower:
                column_mapping[col] = '价格'
        
        if column_mapping:
            price_df = price_df.rename(columns=column_mapping)
        
        print(f"💰 [NEW-QUOTE] 价格表准备完成，共{len(price_df)}行价格数据")
        
        # 步骤3: 最后生成标准型号（合并所有单元格信息）
        print("🔧 [NEW-QUOTE] 步骤3: 最后生成标准型号 - 合并所有单元格信息...")
        
        models = []
        for index, row in df.iterrows():
            if pd.isna(row['品名']) or row['品名'] == '合计':
                models.append('')
                continue
            
            # 合并同一行的所有单元格信息 - 真正的所有单元格，包括备注等
            all_cell_info = []
            
            print(f"🔍 [NEW-QUOTE] 第{index+1}行所有列信息:")
            for col in df.columns:
                cell_value = row[col]
                print(f"   列'{col}': {cell_value}")
                if pd.notna(cell_value) and str(cell_value).strip():
                    cell_str = str(cell_value).strip()
                    # 避免重复添加相同信息
                    if cell_str not in all_cell_info:
                        all_cell_info.append(cell_str)
                        print(f"   ✅ 添加到合并信息: {cell_str}")
                    else:
                        print(f"   ⚪ 跳过重复信息: {cell_str}")
            
            print(f"📋 [NEW-QUOTE] 第{index+1}行合并了所有单元格，包括备注、数量、单位等: {len(all_cell_info)}个有效信息")
            
            # 将所有单元格信息合并为一个完整的字符串
            combined_info = ' '.join(all_cell_info)
            print(f"🔧 [NEW-QUOTE] 第{index+1}行所有单元格合并信息: {combined_info}")
            
            # 使用合并后的完整信息生成标准型号
            model = parse_valve_info_from_combined(combined_info, username, True)
            models.append(model)
            print(f"✅ [NEW-QUOTE] 第{index+1}行标准型号生成: {combined_info} -> {model}")
        
        # 添加标准型号列
        df['标准型号'] = models
        
        # 保存带有标准型号的询价表
        model_csv = os.path.join(output_dir, "inquiry_with_models.csv")
        safe_to_csv(df, model_csv)
        print(f"📋 [NEW-QUOTE] 标准型号生成完成，已保存到: {model_csv}")
        
        # 步骤4: 基于生成的标准型号匹配价格
        print("💰 [NEW-QUOTE] 步骤4: 基于标准型号匹配价格...")
        
        # 使用生成的标准型号进行价格匹配
        result_file = process_inquiry_file(model_csv, price_df)
        
        if result_file and os.path.exists(result_file):
            print(f"🎉 [NEW-QUOTE] 报价生成成功: {result_file}")
            return result_file
        else:
            raise Exception("价格匹配失败，未生成有效报价文件")
            
    except Exception as e:
        print(f"❌ [NEW-QUOTE] 报价生成失败: {e}")
        raise e

if __name__ == "__main__":
    # 测试函数
    print("🧪 测试新顺序的报价生成流程")