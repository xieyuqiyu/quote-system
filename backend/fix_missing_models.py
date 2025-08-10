#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复"未找到匹配"的阀门标准型号

此脚本专门处理询价表中显示"未找到匹配"的阀门，
通过改进的算法生成正确的标准型号。
"""

import os
import pandas as pd
import re
from valve_model_generator import parse_valve_info

def fix_missing_models(input_file, output_file=None):
    """
    修复表格中的"未找到匹配"的阀门标准型号
    
    参数:
        input_file: 输入文件路径（Excel或CSV）
        output_file: 输出文件路径（如不提供则覆盖原文件）
    """
    print(f"\n{'='*80}")
    print(f"开始修复未找到匹配的阀门标准型号")
    print(f"输入文件: {input_file}")
    
    # 如果未提供输出文件，则覆盖原文件
    if not output_file:
        output_file = input_file
    
    # 读取输入文件
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    else:
        df = pd.read_excel(input_file)
    
    print(f"读取文件成功，共 {len(df)} 行数据")
    
    # 统计未找到匹配的行数
    missing_count = 0
    fixed_count = 0
    
    # 准备一个新的标准型号列表
    new_models = []
    
    # 处理每一行
    for index, row in df.iterrows():
        # 检查标准型号列是否存在并且为"未找到匹配"
        if '标准型号' in df.columns:
            current_model = str(row['标准型号'])
            is_missing = '未找到' in current_model or not current_model.strip()
        else:
            # 如果不存在标准型号列，假设所有行都需要修复
            is_missing = True
            current_model = ''
        
        # 如果需要修复
        if is_missing:
            missing_count += 1
            
            # 合并所有单元格信息，增加成功率
            all_cell_info = []
            for col in df.columns:
                cell_value = row[col]
                if pd.notna(cell_value) and str(cell_value).strip() != '':
                    all_cell_info.append(str(cell_value).strip())
            
            # 合并为单一文本
            merged_text = ' '.join(all_cell_info)
            print(f"\n处理第{index+1}行数据:")
            print(f"合并的单元格信息: '{merged_text}'")
            
            # 使用改进后的算法生成标准型号
            try:
                new_model = parse_valve_info(merged_text, '', None, True)
                
                # 检查生成的型号是否有效
                if new_model and len(new_model) > 5:  # 有效的型号至少应该有5个字符
                    fixed_count += 1
                    new_models.append(new_model)
                    print(f"行 {index+1}: 修复成功! -> '{new_model}'")
                else:
                    # 如果生成的型号无效，保留原值
                    new_models.append(current_model)
                    print(f"行 {index+1}: 修复失败! -> '{new_model}'")
            except Exception as e:
                # 发生错误，保留原值
                new_models.append(current_model)
                print(f"行 {index+1}: 处理错误! {str(e)}")
        else:
            # 不需要修复，保留原值
            new_models.append(current_model)
    
    # 更新标准型号列
    if '标准型号' in df.columns:
        df['标准型号'] = new_models
    else:
        df['标准型号'] = new_models
    
    # 保存修复后的文件
    if output_file.endswith('.csv'):
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
    else:
        df.to_excel(output_file, index=False)
    
    print(f"\n修复完成!")
    print(f"总行数: {len(df)}")
    print(f"未找到匹配数: {missing_count}")
    print(f"成功修复数: {fixed_count}")
    print(f"修复率: {fixed_count/missing_count*100:.1f}%" if missing_count > 0 else "无需修复的行")
    print(f"已保存到: {output_file}")
    print(f"{'='*80}")
    
    return output_file

if __name__ == "__main__":
    import sys
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        fix_missing_models(input_file, output_file)
    else:
        print("使用方法: python fix_missing_models.py 输入文件 [输出文件]")
        
        # 提示用户输入文件路径
        input_file = input("请输入需要修复的文件路径: ").strip()
        if input_file:
            output_file = input("请输入输出文件路径 (留空则覆盖原文件): ").strip()
            if not output_file:
                output_file = None
            fix_missing_models(input_file, output_file) 