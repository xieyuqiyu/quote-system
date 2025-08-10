import os
import pandas as pd
import csv
import re
import shutil
from pathlib import Path
from csv_utils import safe_read_csv, safe_to_csv

# 定义文件路径
price_file = './规范后的价格对照表数据/价格.csv'
inquiry_dir = './型号编码后的询价表数据'
output_dir = './报价数据'

# 创建输出目录（如果不存在）
os.makedirs(output_dir, exist_ok=True)

def extract_dn_value(spec):
    """从规格中提取DN值"""
    if pd.isna(spec):
        return ""
        
    # 尝试匹配 DN 值，如 DN50 或 DN50、PN10
    dn_match = re.search(r'DN(\d+)', spec)
    if dn_match:
        return f"DN{dn_match.group(1)}"
    
    # 也可能是格式如 "DN50、PN10、铜"
    parts = spec.split('、')
    for part in parts:
        if part.startswith('DN'):
            return part
            
    return ""

def standardize_model_code(model_code):
    """标准化型号代码，去除空格和其他干扰字符"""
    if pd.isna(model_code) or model_code == "":
        return ""
    
    # 去除空格
    model_code = str(model_code).strip()
    
    # 替换中文括号为英文括号
    model_code = model_code.replace('（', '(').replace('）', ')')
    
    return model_code

def match_model(std_model, spec, price_df):
    """根据标准型号和规格匹配价格表中的条目"""
    if pd.isna(std_model) or std_model == "":
        return None, None
    
    std_model = standardize_model_code(std_model)
    
    # 从规格中提取 DN 值
    dn_value = extract_dn_value(spec)
    if not dn_value:
        return None, None
    
    # 查找匹配的型号和规格
    # 第一种方法：尝试直接匹配标准型号部分（如Z41X-16Q）
    matching_prices = price_df[(price_df['型号'].str.contains(std_model, regex=False, na=False)) & 
                              (price_df['规格'] == dn_value)]
    
    # 如果没找到，尝试更宽松的匹配方式
    if matching_prices.empty:
        # 提取标准型号中的关键部分（通常是字母和数字的组合，如Z41X-16Q）
        key_part_match = re.search(r'([A-Z0-9]+[-][A-Z0-9]+)', std_model)
        if key_part_match:
            key_part = key_part_match.group(1)
            matching_prices = price_df[(price_df['型号'].str.contains(key_part, regex=False, na=False)) & 
                                     (price_df['规格'] == dn_value)]
    
    # 如果仍然没找到，尝试匹配型号中的主要部分（如Z41X）
    if matching_prices.empty:
        base_model_match = re.search(r'([A-Z]+\d+[A-Z]+)', std_model)
        if base_model_match:
            base_model = base_model_match.group(1)
            matching_prices = price_df[(price_df['型号'].str.contains(base_model, regex=False, na=False)) & 
                                     (price_df['规格'] == dn_value)]
    
    if not matching_prices.empty:
        # 如果有多个品牌，返回所有品牌的价格
        result = {}
        for _, row in matching_prices.iterrows():
            brand = row['品牌']
            price = row['价格']
            # 确保价格是一个数值
            try:
                if not pd.isna(price):
                    # 如果价格是字符串但实际是另一个品牌名称，跳过
                    if isinstance(price, str) and price in ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '上海科尼特', '上海科尼菲']:
                        continue
                    result[brand] = float(price)
            except (ValueError, TypeError):
                # 如果转换失败，跳过这个价格
                continue
        
        if result:  # 只有当至少有一个有效价格时才返回
            return matching_prices['型号'].iloc[0], result
    
    return None, None

def process_inquiry_file(file_path, price_df):
    """处理单个询价文件，生成报价"""
    print(f"\n{'='*80}")
    print(f"📋 [DEBUG] process_inquiry_file 开始")
    print(f"📁 [DEBUG] 文件路径: {file_path}")
    print(f"💰 [DEBUG] 价格表行数: {len(price_df)}")
    print(f"{'='*80}")
    
    try:
        # 使用安全的CSV读取函数
        inquiry_df = safe_read_csv(file_path)
        print(f"📊 [DEBUG] 询价表读取成功，行数: {len(inquiry_df)}")
        print(f"📋 [DEBUG] 询价表列名: {list(inquiry_df.columns)}")
        
        # 添加报价列
        for brand in ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '上海科尼特']:
            inquiry_df[f'{brand}价格'] = None
            inquiry_df[f'{brand}总价'] = None
        
        inquiry_df['匹配型号'] = None
        inquiry_df['匹配结果'] = None
        
        print(f"📋 [DEBUG] 添加报价列完成")
        
        # 遍历每一行
        for idx, row in inquiry_df.iterrows():
            print(f"\n🔍 [DEBUG] 处理第 {idx+1} 行:")
            std_model = row.get('标准型号', '')
            spec = row.get('规格型号', '')
            product_name = row.get('品名', '')
            
            print(f"   品名: '{product_name}'")
            print(f"   规格型号: '{spec}'")
            print(f"   标准型号: '{std_model}'")
            
            matched_model, prices = match_model(std_model, spec, price_df)
            
            print(f"🔍 [DEBUG] 匹配结果:")
            print(f"   匹配型号: {matched_model}")
            print(f"   匹配价格: {prices}")
            
            if matched_model and prices:
                inquiry_df.at[idx, '匹配型号'] = matched_model
                inquiry_df.at[idx, '匹配结果'] = '成功'
                
                print(f"✅ [DEBUG] 匹配成功，填充价格:")
                # 填充各品牌价格
                for brand, price in prices.items():
                    col_name = f'{brand}价格'
                    if col_name in inquiry_df.columns:
                        inquiry_df.at[idx, col_name] = price
                        print(f"   {brand}: {price}")
                        
                        # 计算总价
                        if not pd.isna(row.get('数量', 0)):
                            try:
                                quantity = float(row['数量'])
                                total_price = price * quantity
                                inquiry_df.at[idx, f'{brand}总价'] = total_price
                                print(f"   {brand}总价: {total_price} (数量: {quantity})")
                            except (ValueError, TypeError):
                                print(f"   {brand}总价计算失败: 数量格式错误")
            else:
                inquiry_df.at[idx, '匹配结果'] = '未找到匹配'
                print(f"❌ [DEBUG] 匹配失败")
        
        # 添加汇总行
        print(f"\n📊 [DEBUG] 添加汇总行")
        summary_row = {'品名': '总计'}
        for brand in ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '上海科尼特']:
            total_col = f'{brand}总价'
            if total_col in inquiry_df.columns:
                total = inquiry_df[total_col].sum(skipna=True)
                summary_row[total_col] = total
                print(f"   {brand}总价: {total}")
        
        # 将汇总行添加到数据框
        summary_df = pd.DataFrame([summary_row])
        inquiry_df = pd.concat([inquiry_df, summary_df], ignore_index=True)
        
        # 重新排列列的顺序，确保标准型号列在显著位置
        columns_order = []
        
        # 基础信息列
        if '品名' in inquiry_df.columns:
            columns_order.append('品名')
        if '规格型号' in inquiry_df.columns:
            columns_order.append('规格型号')
        if '标准型号' in inquiry_df.columns:
            columns_order.append('标准型号')
        if '数量' in inquiry_df.columns:
            columns_order.append('数量')
        if '单位' in inquiry_df.columns:
            columns_order.append('单位')
        
        # 匹配结果列
        if '匹配型号' in inquiry_df.columns:
            columns_order.append('匹配型号')
        if '匹配结果' in inquiry_df.columns:
            columns_order.append('匹配结果')
        
        # 价格列
        for brand in ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '上海科尼特']:
            price_col = f'{brand}价格'
            total_col = f'{brand}总价'
            if price_col in inquiry_df.columns:
                columns_order.append(price_col)
            if total_col in inquiry_df.columns:
                columns_order.append(total_col)
        
        # 添加其他剩余列
        for col in inquiry_df.columns:
            if col not in columns_order:
                columns_order.append(col)
        
        # 重新排列数据框
        inquiry_df = inquiry_df[columns_order]
        
        # 保存报价结果
        output_filename = os.path.join(output_dir, f"报价_{os.path.basename(file_path)}")
        
        # 保存为Excel格式以便更好地显示
        if output_filename.endswith('.csv'):
            excel_filename = output_filename.replace('.csv', '.xlsx')
        else:
            excel_filename = output_filename + '.xlsx'
        
        try:
            inquiry_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f"💾 [DEBUG] 报价保存成功 (Excel): {excel_filename}")
            
            # 同时保存CSV版本
            safe_to_csv(inquiry_df, output_filename)
            print(f"💾 [DEBUG] 报价保存成功 (CSV): {output_filename}")
            
            print(f"📋 [DEBUG] 最终输出列顺序: {list(inquiry_df.columns)}")
            print(f"{'='*80}")
            
            return excel_filename  # 返回Excel文件路径
        except Exception as e:
            print(f"⚠️ [DEBUG] Excel保存失败，使用CSV: {e}")
            safe_to_csv(inquiry_df, output_filename)
            print(f"💾 [DEBUG] 报价保存成功 (CSV): {output_filename}")
            print(f"{'='*80}")
            return output_filename
    except Exception as e:
        print(f"❌ [DEBUG] 处理文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}")
        return None

def generate_summary_report(processed_files):
    """生成汇总报告"""
    summary_file = os.path.join(output_dir, "报价汇总.csv")
    
    # 创建汇总数据框
    summary_data = []
    
    for file in processed_files:
        if file:
            try:
                df = safe_read_csv(file)
                # 获取最后一行（总计行）
                if not df.empty:
                    last_row = df.iloc[-1].to_dict()
                    last_row['文件名'] = os.path.basename(file)
                    summary_data.append(last_row)
            except Exception as e:
                print(f"处理汇总文件 {file} 时出错: {str(e)}")
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        safe_to_csv(summary_df, summary_file)
        print(f"汇总报告已保存至: {summary_file}")

def main():
    """主函数，处理所有询价文件"""
    print("开始生成报价...")
    
    try:
        # 使用安全的CSV读取函数加载价格数据
        price_df = safe_read_csv(price_file)
        print(f"已加载价格数据，共 {len(price_df)} 条记录")
        
        # 处理所有询价文件
        inquiry_files = [f for f in os.listdir(inquiry_dir) if f.endswith('.csv')]
        print(f"找到 {len(inquiry_files)} 个询价文件待处理")
        
        processed_files = []
        for file in inquiry_files:
            file_path = os.path.join(inquiry_dir, file)
            output_file = process_inquiry_file(file_path, price_df)
            if output_file:
                processed_files.append(output_file)
        
        # 生成汇总报告
        if processed_files:
            generate_summary_report(processed_files)
        
        print("报价生成完成！")
    except Exception as e:
        print(f"程序运行出错: {str(e)}")

if __name__ == "__main__":
    main() 