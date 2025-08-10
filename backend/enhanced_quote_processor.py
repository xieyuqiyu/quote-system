"""
增强的报价处理器 - 集成改进的价格匹配功能
"""
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from improved_price_matcher import ImprovedPriceMatcher
from csv_utils import safe_read_csv, safe_to_csv

def process_quote_with_enhanced_matching(inquiry_file, price_file, output_file, username=None):
    """
    使用增强的价格匹配功能处理报价
    
    Args:
        inquiry_file: 询价表文件路径
        price_file: 价格表文件路径  
        output_file: 输出文件路径
        username: 用户名
    
    Returns:
        str: 输出文件路径，如果失败返回None
    """
    try:
        print(f"🚀 [ENHANCED] 开始增强报价处理")
        print(f"📋 [ENHANCED] 询价文件: {inquiry_file}")
        print(f"💰 [ENHANCED] 价格文件: {price_file}")
        print(f"📄 [ENHANCED] 输出文件: {output_file}")
        
        # 检查文件是否存在
        if not os.path.exists(inquiry_file):
            raise FileNotFoundError(f"询价文件不存在: {inquiry_file}")
        
        if not os.path.exists(price_file):
            raise FileNotFoundError(f"价格文件不存在: {price_file}")
        
        # 创建价格匹配器
        matcher = ImprovedPriceMatcher()
        
        # 加载价格表
        if not matcher.load_price_table(price_file):
            raise Exception("价格表加载失败")
        
        # 读取询价表
        print(f"📊 [ENHANCED] 读取询价表...")
        if inquiry_file.endswith('.csv'):
            inquiry_df = safe_read_csv(inquiry_file)
        else:
            inquiry_df = pd.read_excel(inquiry_file)
        
        print(f"📋 [ENHANCED] 询价表读取成功: {len(inquiry_df)} 行数据")
        print(f"📋 [ENHANCED] 询价表列名: {list(inquiry_df.columns)}")
        
        # 标准化询价表列名
        inquiry_df = standardize_inquiry_columns(inquiry_df)
        
        # 使用改进的匹配器处理询价表
        result_df = matcher.process_inquiry_with_totals(inquiry_df)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存结果
        if output_file.endswith('.csv'):
            safe_to_csv(result_df, output_file)
        else:
            result_df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"✅ [ENHANCED] 报价处理完成，结果保存到: {output_file}")
        
        # 打印统计信息
        total_rows = len(result_df) - 1  # 减去合计行
        matched_rows = len(result_df[result_df['匹配状态'].str.contains('成功', na=False)])
        total_amount = result_df['总价'].sum(skipna=True)
        
        print(f"📊 [ENHANCED] 处理统计:")
        print(f"   总行数: {total_rows}")
        print(f"   匹配成功: {matched_rows}")
        print(f"   匹配率: {matched_rows/total_rows*100:.1f}%")
        print(f"   总金额: ¥{total_amount:.2f}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ [ENHANCED] 报价处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def standardize_inquiry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """标准化询价表列名"""
    column_mapping = {}
    
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        
        # 品名列映射
        if any(keyword in col_lower for keyword in ['品名', 'product', '产品', '名称']):
            column_mapping[col] = '品名'
        # 规格型号列映射
        elif any(keyword in col_lower for keyword in ['规格', 'spec', '型号', 'model']):
            column_mapping[col] = '规格型号'
        # 数量列映射
        elif any(keyword in col_lower for keyword in ['数量', 'quantity', 'qty', '个数']):
            column_mapping[col] = '数量'
        # 工作量列映射
        elif any(keyword in col_lower for keyword in ['工作量', '工时', '人工', '工日', '工作日', '工作', 'workload', 'man-hour', 'labor']):
            column_mapping[col] = '工作量'
        # 单位列映射
        elif any(keyword in col_lower for keyword in ['单位', 'unit']):
            column_mapping[col] = '单位'
        # 标准型号列映射
        elif any(keyword in col_lower for keyword in ['标准型号', 'standard']):
            column_mapping[col] = '标准型号'
    
    if column_mapping:
        df = df.rename(columns=column_mapping)
        print(f"📋 [ENHANCED] 询价表列名映射: {column_mapping}")
    
    return df

def generate_multi_brand_quote(inquiry_file, price_files, output_file, username=None):
    """
    生成多品牌价格对比报价单
    
    Args:
        inquiry_file: 询价表文件路径
        price_files: 价格表文件路径列表 (dict: {company_name: file_path})
        output_file: 输出文件路径
        username: 用户名
    
    Returns:
        str: 输出文件路径，如果失败返回None
    """
    try:
        print(f"🚀 [MULTI] 开始多品牌报价处理")
        print(f"📋 [MULTI] 询价文件: {inquiry_file}")
        print(f"💰 [MULTI] 价格文件数量: {len(price_files)}")
        
        # 读取询价表
        if inquiry_file.endswith('.csv'):
            inquiry_df = safe_read_csv(inquiry_file)
        else:
            inquiry_df = pd.read_excel(inquiry_file)
        
        inquiry_df = standardize_inquiry_columns(inquiry_df)
        
        # 为每个公司创建价格列
        company_results = {}
        
        for company_name, price_file_path in price_files.items():
            print(f"\n🏢 [MULTI] 处理公司: {company_name}")
            
            if not os.path.exists(price_file_path):
                print(f"⚠️ [MULTI] 价格文件不存在: {price_file_path}")
                continue
            
            # 创建匹配器
            matcher = ImprovedPriceMatcher()
            
            if not matcher.load_price_table(price_file_path):
                print(f"❌ [MULTI] {company_name} 价格表加载失败")
                continue
            
            # 为每行产品匹配价格
            company_prices = []
            company_totals = []
            
            for idx, row in inquiry_df.iterrows():
                # 跳过合计行
                if pd.isna(row.get('品名')) or str(row.get('品名')).strip() in ['合计', '总计', '']:
                    company_prices.append('')
                    company_totals.append('')
                    continue
                
                product_name = str(row.get('品名', ''))
                specification = str(row.get('规格型号', ''))
                model_code = str(row.get('标准型号', ''))
                quantity = row.get('数量', 1)
                
                # 匹配产品
                match_result = matcher.match_product(product_name, specification, model_code)
                
                if match_result['success']:
                    best_match = match_result['best_match']
                    price = best_match['价格']
                    company_prices.append(price)
                    
                    # 计算总价
                    try:
                        if not pd.isna(quantity) and quantity != '':
                            qty = float(quantity)
                            total = price * qty
                        else:
                            total = 0.0  # 数量为空时，总价设为0
                        company_totals.append(total)
                    except (ValueError, TypeError):
                        company_totals.append(0.0)  # 计算失败时，总价设为0
                else:
                    company_prices.append('')
                    company_totals.append('')
            
            company_results[company_name] = {
                'prices': company_prices,
                'totals': company_totals
            }
        
        # 构建最终的报价表
        result_df = inquiry_df.copy()
        
        # 添加各公司的价格和总价列
        for company_name, data in company_results.items():
            result_df[f'{company_name}_单价'] = data['prices']
            result_df[f'{company_name}_总价'] = data['totals']
        
        # 添加最优价格列
        price_columns = [f'{company}_单价' for company in company_results.keys()]
        total_columns = [f'{company}_总价' for company in company_results.keys()]
        
        if price_columns:
            # 计算最低单价
            result_df['最低单价'] = result_df[price_columns].min(axis=1, skipna=True)
            result_df['最低总价'] = result_df[total_columns].min(axis=1, skipna=True)
            
            # 标识最优供应商
            best_suppliers = []
            for idx, row in result_df.iterrows():
                min_price = row['最低单价']
                best_supplier = ''
                
                if not pd.isna(min_price) and min_price > 0:
                    for company in company_results.keys():
                        if row[f'{company}_单价'] == min_price:
                            best_supplier = company
                            break
                
                best_suppliers.append(best_supplier)
            
            result_df['最优供应商'] = best_suppliers
        
        # 添加合计行
        summary_row = {'品名': '合计'}
        
        for company_name in company_results.keys():
            total_col = f'{company_name}_总价'
            if total_col in result_df.columns:
                total = result_df[total_col].sum(skipna=True)
                summary_row[total_col] = total
        
        if '最低总价' in result_df.columns:
            summary_row['最低总价'] = result_df['最低总价'].sum(skipna=True)
        
        # 添加合计行
        summary_df = pd.DataFrame([summary_row])
        result_df = pd.concat([result_df, summary_df], ignore_index=True)
        
        # 保存结果
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        if output_file.endswith('.csv'):
            safe_to_csv(result_df, output_file)
        else:
            result_df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"✅ [MULTI] 多品牌报价处理完成，结果保存到: {output_file}")
        
        # 打印统计信息
        print(f"📊 [MULTI] 处理统计:")
        print(f"   参与公司数: {len(company_results)}")
        for company_name in company_results.keys():
            total_col = f'{company_name}_总价'
            if total_col in result_df.columns:
                company_total = result_df[total_col].sum(skipna=True)
                print(f"   {company_name}总价: ¥{company_total:.2f}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ [MULTI] 多品牌报价处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None