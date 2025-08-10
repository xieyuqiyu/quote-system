import pandas as pd
import os

def validate_price_table_format(df):
    """
    验证价格表格式是否符合要求
    
    Args:
        df: pandas DataFrame，价格表数据
        
    Returns:
        dict: 包含验证结果和错误信息
        {
            'is_valid': bool,
            'errors': list,
            'brands': list,
            'message': str
        }
    """
    required_columns = ['产品名称', '型号', '规格', '单价', '品牌']
    errors = []
    brands = []
    
    print(f"🔍 [VALIDATE] 开始验证价格表格式")
    print(f"   列数: {len(df.columns)}")
    print(f"   行数: {len(df)}")
    print(f"   列名: {list(df.columns)}")
    
    # 1. 检查必需字段
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"缺少必需字段: {', '.join(missing_columns)}")
        print(f"❌ 缺少字段: {missing_columns}")
    else:
        print(f"✅ 所有必需字段都存在")
    
    # 2. 检查数据行数
    if len(df) == 0:
        errors.append("价格表为空，没有数据行")
        print(f"❌ 价格表为空")
    else:
        print(f"✅ 数据行数: {len(df)}")
    
    # 3. 检查品牌列
    if '品牌' in df.columns:
        brand_values = df['品牌'].dropna().unique()
        if len(brand_values) == 0:
            errors.append("品牌列中没有有效数据")
            print(f"❌ 品牌列为空")
        else:
            brands = [str(brand).strip() for brand in brand_values if str(brand).strip() and str(brand) != 'nan']
            print(f"✅ 找到品牌: {brands}")
    else:
        errors.append("缺少品牌列")
        print(f"❌ 缺少品牌列")
    
    # 4. 检查单价列
    if '单价' in df.columns:
        try:
            # 尝试转换为数字
            price_values = pd.to_numeric(df['单价'], errors='coerce')
            invalid_prices = df[price_values.isna()]['单价']
            if len(invalid_prices) > 0:
                errors.append(f"单价列包含非数字数据: {list(invalid_prices.unique())}")
                print(f"❌ 单价列包含非数字数据")
            else:
                print(f"✅ 单价列格式正确")
        except Exception as e:
            errors.append(f"单价列格式错误: {str(e)}")
            print(f"❌ 单价列格式错误: {e}")
    else:
        errors.append("缺少单价列")
        print(f"❌ 缺少单价列")
    
    # 5. 检查其他必需字段
    for col in ['产品名称', '型号', '规格']:
        if col in df.columns:
            empty_count = df[col].isna().sum()
            if empty_count == len(df):
                errors.append(f"{col}列全部为空")
                print(f"❌ {col}列全部为空")
            else:
                print(f"✅ {col}列有数据")
        else:
            errors.append(f"缺少{col}列")
            print(f"❌ 缺少{col}列")
    
    # 6. 生成结果
    is_valid = len(errors) == 0
    if is_valid:
        message = f"价格表格式验证通过！找到 {len(brands)} 个品牌"
    else:
        message = f"价格表格式验证失败，发现 {len(errors)} 个问题"
    
    result = {
        'is_valid': is_valid,
        'errors': errors,
        'brands': brands,
        'message': message
    }
    
    print(f"🔍 [VALIDATE] 验证结果: {result}")
    return result

def extract_brands_from_price_table(file_path):
    """
    从价格表中提取品牌信息
    
    Args:
        file_path: str, 价格表文件路径
        
    Returns:
        list: 品牌列表
    """
    try:
        df = pd.read_excel(file_path)
        if '品牌' in df.columns:
            brand_values = df['品牌'].dropna().unique()
            brands = [str(brand).strip() for brand in brand_values if str(brand).strip() and str(brand) != 'nan']
            return brands
        else:
            return []
    except Exception as e:
        print(f"❌ 读取价格表失败: {e}")
        return [] 