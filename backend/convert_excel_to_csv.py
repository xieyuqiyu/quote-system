# 只保留主流程相关内容
import os
import pandas as pd
import glob
import re
import traceback
import datetime

def detect_table_structure(df):
    header_row = None
    valve_keywords = ['阀门', '闸阀', '球阀', '蝶阀', '止回阀', '过滤器', '品名', '型号', 'DN']
    for i in range(min(15, len(df))):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if str(x) != 'nan'])
        if any(keyword in row_str for keyword in valve_keywords):
            header_row = i
            break
    if header_row is None:
        for i in range(min(20, len(df))):
            if df.iloc[i].notna().sum() > 2:
                header_row = i
                break
    if header_row is None:
        header_row = 0
    return header_row

def find_quantity_column(df):
    quantity_col = None
    for col in range(df.shape[1]):
        numbers_count = 0
        non_numbers_count = 0
        for row in range(df.shape[0]):
            if pd.isna(df.iloc[row, col]):
                continue
            cell_value = str(df.iloc[row, col]).strip()
            if re.match(r'^[0-9]+(\.[0-9]+)?$', cell_value):
                numbers_count += 1
            else:
                non_numbers_count += 1
        if numbers_count > 5 and numbers_count > non_numbers_count * 2:
            quantity_col = col
            print(f"找到可能的数量列: 列索引={quantity_col}, 数字数量={numbers_count}")
            return quantity_col
    return None

def standardize_columns(df):
    """标准化列名，但保留所有原始列"""
    standard_columns = {
        '品名': ['品名', '项目名称', '项 目', '名称', '阀门', '名称及规格', '品种', '项目名称及技术参数', 'B'],
        '规格型号': ['规格型号', '规格', '型号', '口径', 'DN', '公称直径', '规格参数', 'C'],
        '计量单位': ['计量单位', '单位', '单 位', 'D'],
        '数量': ['数量', '数 量', '套数', '个数', '数  量', 'E', '个','工作量']
    }
    
    # 创建列名映射
    column_mapping = {}
    for std_col, variations in standard_columns.items():
        for var in variations:
            column_mapping[var] = std_col
    
    # 重命名列，但保留所有原始列
    new_columns = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in column_mapping:
            new_columns[col] = column_mapping[col_str]
            continue
        for orig, std in column_mapping.items():
            if orig in col_str:
                new_columns[col] = std
                break
    
    # 重命名列
    renamed_df = df.rename(columns=new_columns)
    
    # 确保所有必需的标准化列都存在
    required_columns = ['品名', '规格型号', '计量单位', '数量']
    for col in required_columns:
        if col not in renamed_df.columns:
            renamed_df[col] = [''] * len(renamed_df)
    
    # 确保品名编码列存在
    if '品名编码' not in renamed_df.columns:
        renamed_df['品名编码'] = [''] * len(renamed_df)
    
    return renamed_df

def parse_specs_from_details(details_text):
    if not details_text or pd.isna(details_text):
        return None, None, None, None
    details_text = str(details_text)
    valve_type = None
    dn_size = None
    pn_rating = None
    material = None
    type_match = re.search(r'品[种类][:：]?\s*([^,，\d\n]+)', details_text)
    if type_match:
        valve_type = type_match.group(1).strip()
    dn_match = re.search(r'公称直径[D]?N\(mm\)[:：]?\s*(\d+)', details_text)
    if dn_match:
        dn_size = dn_match.group(1).strip()
    else:
        dn_match = re.search(r'DN\(mm\)[:：]?\s*(\d+)', details_text)
        if dn_match:
            dn_size = dn_match.group(1).strip()
        else:
            dn_match = re.search(r'DN\s*[:：]?\s*(\d+)', details_text)
            if dn_match:
                dn_size = dn_match.group(1).strip()
            else:
                dn_match = re.search(r'DN(\d+)', details_text)
                if dn_match:
                    dn_size = dn_match.group(1).strip()
    pn_match = re.search(r'公称压力PN\(MPa\)[:：]?\s*([\d\.]+)', details_text)
    if pn_match:
        pn_value = float(pn_match.group(1).strip())
        pn_rating = str(int(pn_value * 10))
    else:
        pn_match = re.search(r'PN\(MPa\)[:：]?\s*([\d\.]+)', details_text)
        if pn_match:
            pn_value = float(pn_match.group(1).strip())
            pn_rating = str(int(pn_value * 10))
        else:
            pn_match = re.search(r'PN\s*[:：]?\s*([\d\.]+)', details_text)
            if pn_match:
                pn_str = pn_match.group(1).strip()
                if '.' in pn_str and float(pn_str) < 10:
                    pn_value = float(pn_str)
                    pn_rating = str(int(pn_value * 10))
                else:
                    pn_rating = pn_str
            else:
                pn_match = re.search(r'PN(\d+)', details_text)
                if pn_match:
                    pn_rating = pn_match.group(1).strip()
    material_match = re.search(r'材[料质][:：]?\s*([^,，\d\n]+)', details_text)
    if material_match:
        material = material_match.group(1).strip()
    else:
        material_match = re.search(r'阀体材[料质][:：]?\s*([^,，\d\n]+)', details_text)
        if material_match:
            material = material_match.group(1).strip()
    return valve_type, dn_size, pn_rating, material

def extract_valve_info(df, quantity_col=None):
    result_rows = []
    has_categories = False
    current_category = ""
    for i in range(len(df)):
        row = df.iloc[i]
        if len(row) >= 3 and pd.notna(row.iloc[0]) and pd.isna(row.iloc[2]):
            potential_category = str(row.iloc[0]).strip()
            if "阀门" in potential_category or "消防" in potential_category:
                has_categories = True
                break
    for i in range(len(df)):
        row = df.iloc[i]
        if row.isna().all() or (pd.notna(row.iloc[0]) and all(pd.isna(x) for x in row.iloc[1:])):
            continue
        if has_categories and pd.notna(row.iloc[0]) and all(pd.isna(x) for x in row.iloc[1:3] if len(row) > 3):
            potential_category = str(row.iloc[0]).strip()
            if len(potential_category) > 0 and (("阀门" in potential_category) or ("水" in potential_category)):
                current_category = potential_category
            continue
        valve_name = ""
        specs = ""
        unit = "个"
        quantity = "1"
        if quantity_col is not None and 0 <= quantity_col < len(row) and pd.notna(row.iloc[quantity_col]):
            quantity_val = str(row.iloc[quantity_col]).strip()
            if re.match(r'^[0-9]+(\.[0-9]+)?$', quantity_val):
                quantity = quantity_val
        if has_categories and len(row) >= 3:
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                valve_name = str(row.iloc[0]).strip()
                if pd.notna(row.iloc[1]):
                    specs = str(row.iloc[1]).strip()
                if quantity_col is None and len(row) >= 3 and pd.notna(row.iloc[2]) and re.match(r'^\d+(\.\d+)?$', str(row.iloc[2]).strip()):
                    quantity = str(row.iloc[2]).strip()
        if not valve_name or not specs:
            for j, val in enumerate(row):
                if pd.isna(val):
                    continue
                val_str = str(val).strip()
                if "、" in val_str and ("品种" in val_str or "公称" in val_str or "材质" in val_str):
                    valve_type, dn_size, pn_rating, material = parse_specs_from_details(val_str)
                    if valve_type and not valve_name:
                        valve_name = valve_type
                    if dn_size and pn_rating:
                        specs = f"DN{dn_size}、PN{pn_rating}"
                        if material:
                            specs += f"、{material}"
                    elif dn_size:
                        specs = f"DN{dn_size}"
                        if material:
                            specs += f"、{material}"
                    if quantity_col is None or j != quantity_col:
                        if j+1 < len(row) and pd.notna(row.iloc[j+1]) and re.match(r'^\d+(\.\d+)?$', str(row.iloc[j+1]).strip()):
                            quantity = str(row.iloc[j+1]).strip()
                    break
                elif any(keyword in val_str for keyword in ['阀', '球阀', '闸阀', '蝶阀', '止回阀', '过滤器']):
                    valve_name = val_str
                elif 'DN' in val_str or 'PN' in val_str:
                    specs = val_str
                elif quantity_col is None or j != quantity_col:
                    if re.match(r'^\d+(\.\d+)?$', val_str) and j > 1:
                        quantity = val_str
                elif val_str in ['个', '台', '套', '件']:
                    unit = val_str
        if valve_name or specs:
            if current_category and valve_name and "阀门" not in valve_name and "过滤器" not in valve_name and "阀" not in valve_name:
                full_name = f"{current_category}{valve_name}"
            else:
                full_name = valve_name if valve_name else "阀门"
            if not specs and valve_name and "DN" in valve_name:
                dn_match = re.search(r'DN(\d+)', valve_name)
                if dn_match:
                    specs = f"DN{dn_match.group(1)}"
                    if "PN" in valve_name:
                        pn_match = re.search(r'PN(\d+)', valve_name)
                        if pn_match:
                            specs += f"、PN{pn_match.group(1)}"
            result_rows.append({
                '品名编码': '',
                '品名': full_name,
                '规格型号': specs,
                '计量单位': unit,
                '数量': quantity
            })
    return pd.DataFrame(result_rows)

def process_excel_to_standard_csv(input_file, output_file=None, price_file=None, selected_brand=None):
    import pandas as pd
    import os
    import glob
    from valve_model_generator import parse_valve_info
    print(f"[DEBUG] 输入文件: {input_file}")
    if price_file:
        print(f"[DEBUG] 价格文件: {price_file}")
    
    # 1. 读取原始表 - 优先保留原始表头
    try:
        # 首先尝试读取CSV文件
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
            print(f"[DEBUG] 使用CSV读取方式")
        else:
            # 尝试读取Excel文件，优先保留原始表头
            df = pd.read_excel(input_file)
            print(f"[DEBUG] 使用默认Excel读取方式，保留原始表头")
        
        # 检查是否是新的文件结构
        if '品名' in df.columns and '品牌' in df.columns:
            print(f"[DEBUG] 检测到新文件结构")
            # 新文件结构：品名、规格型号、计量单位、数量、单价、总价、品牌、标准型号
            df['项目名称'] = df['品名']
            df['工程量'] = df['数量']
            df['备 注'] = df['品牌']
        
        # 不再使用skiprows=2，保留原始表头
        print(f"[DEBUG] 保留原始表头结构")
        
    except Exception as e:
        # 如果读取失败，记录错误但不使用skiprows
        print(f"[DEBUG] 读取文件时出现异常: {e}")
        raise e
    
    print(f"[DEBUG] 读取后的列名: {list(df.columns)}")
    print(f"[DEBUG] 数据行数: {len(df)}")
    
    # 2. 提取数量列
    quantity_col = None
    for col in df.columns:
        col_str = str(col).strip()
        if '数量' in col_str or '工程量' in col_str or '个' in col_str or '台' in col_str or '套' in col_str:
            quantity_col = col
            print(f"[DEBUG] 找到数量列: {col}")
            break
    
    if quantity_col is None:
        # 如果没找到数量列，尝试通过数据内容识别
        for col_idx, col in enumerate(df.columns):
            numeric_count = 0
            total_count = 0
            for val in df[col].dropna():
                try:
                    float(val)
                    numeric_count += 1
                except:
                    pass
                total_count += 1
            
            if total_count > 0 and numeric_count / total_count > 0.5:
                quantity_col = col
                print(f"[DEBUG] 通过数据内容识别到数量列: {col} (数字比例: {numeric_count}/{total_count})")
                break
    
    if quantity_col:
        df['数量'] = df[quantity_col]
        print(f"[DEBUG] 数量列提取完成，非空数量: {df['数量'].notna().sum()}")
    else:
        df['数量'] = ''
        print("[警告] 未找到数量列")
    
    # 3. 生成标准型号（合并所有单元格，仅用于生成）
    # 修复标准型号生成逻辑
    models = []
    for idx, row in df.iterrows():
        merged = ' '.join([str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() != ''])
        model = parse_valve_info(merged, '', None, True)
        models.append(model if model is not None else '')
    df['标准型号'] = models

    # 4. 补全所有行的规格型号
    if '规格型号' in df.columns:
        # 新文件结构：直接使用规格型号列
        print(f"[DEBUG] 使用现有规格型号列")
        
        # 确保规格型号列为字符串类型
        df['规格型号'] = df['规格型号'].astype(str)
        
        # 从所有单元格提取DN
        for idx, row in df.iterrows():
            spec = row.get('规格型号', '')
            # 检查是否为NaN或空值
            if pd.isna(spec) or spec == '' or str(spec).strip() == '' or str(spec).lower() == 'nan':
                # 从该行的所有单元格中提取DN信息
                found_dn = None
                source_cell = ''
                
                # 遍历该行的所有单元格
                for col_idx, cell_value in enumerate(row):
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip()
                        if 'DN' in cell_str:
                            dn_match = re.search(r'DN\s*(\d+)', cell_str, re.IGNORECASE)
                            if dn_match:
                                found_dn = f'DN{dn_match.group(1)}'
                                source_cell = f"列{col_idx+1}({df.columns[col_idx]})"
                                print(f"[调试] 行{idx+1}: 从{source_cell}提取规格型号: {cell_str} -> {found_dn}")
                                break
                
                # 如果找到了DN，设置到规格型号列
                if found_dn:
                    df.at[idx, '规格型号'] = found_dn
        
        # 将'nan'字符串替换为空字符串（在提取完成后）
        df['规格型号'] = df['规格型号'].replace('nan', '')
    else:
        # 旧文件结构：从所有单元格提取DN
        df['规格型号'] = ''
        for idx, row in df.iterrows():
            # 从该行的所有单元格中提取DN信息
            found_dn = None
            source_cell = ''
            
            # 遍历该行的所有单元格
            for col_idx, cell_value in enumerate(row):
                if pd.notna(cell_value):
                    cell_str = str(cell_value).strip()
                    if 'DN' in cell_str:
                        dn_match = re.search(r'DN\s*(\d+)', cell_str, re.IGNORECASE)
                        if dn_match:
                            found_dn = f'DN{dn_match.group(1)}'
                            source_cell = f"列{col_idx+1}({df.columns[col_idx]})"
                            print(f"[调试] 行{idx+1}: 从{source_cell}提取规格型号: {cell_str} -> {found_dn}")
                            break
            
            # 如果找到了DN，设置到规格型号列
            if found_dn:
                df.at[idx, '规格型号'] = found_dn

    # 5. 品牌库
    brand_list = ["上海沪工", "上海良工", "中核苏阀", "上海泰科", "上海科尼特"]

    # 6. 品牌列：填充品牌信息
    if selected_brand:
        # 如果提供了选择的品牌，直接使用它
        print(f"[DEBUG] 使用选择的品牌: {selected_brand}")
        df['品牌'] = selected_brand
    else:
        # 如果没有提供选择的品牌，使用原有的提取逻辑
        if '品牌' in df.columns:
            # 新文件结构：直接使用品牌列
            print(f"[DEBUG] 使用现有品牌列")
            
            # 确保品牌列为字符串类型
            df['品牌'] = df['品牌'].astype(str)
            # 将'nan'字符串替换为空字符串
            df['品牌'] = df['品牌'].replace('nan', '')
            
            # 检查品牌列是否有空值，如果有则尝试从其他列提取
            for idx, row in df.iterrows():
                brand = row.get('品牌', '')
                if pd.isna(brand) or brand == '' or str(brand).strip() == '' or str(brand).lower() == 'nan':
                    # 尝试从项目名称中提取品牌
                    project_name = str(row.get('项目名称', row.get('品名', ''))).strip()
                    found_brand = ''
                    for brand_name in brand_list:
                        if brand_name in project_name:
                            found_brand = brand_name
                            df.at[idx, '品牌'] = found_brand
                            print(f"[调试] 行{idx+1}: 从项目名称提取品牌: {project_name} -> {found_brand}")
                            break
        else:
            # 旧文件结构：从备 注列提取品牌信息
            df['品牌'] = ''
            for idx, row in df.iterrows():
                remark = str(row.get('备 注', '')).strip()
                remark2 = str(row.get('备 注.1', '')).strip()
                
                # 合并两个备注列
                all_remarks = f"{remark} {remark2}".strip()
                
                found_brand = ''
                for brand in brand_list:
                    if brand in all_remarks:
                        found_brand = brand
                        print(f"[调试] 行{idx+1}: 从备注提取品牌: {all_remarks} -> {brand}")
                        break
                
                # 如果没有找到品牌，尝试从项目名称中提取
                if not found_brand:
                    project_name = str(row.get('项目名称', '')).strip()
                    for brand in brand_list:
                        if brand in project_name:
                            found_brand = brand
                            print(f"[调试] 行{idx+1}: 从项目名称提取品牌: {project_name} -> {brand}")
                            break
                
                df.at[idx, '品牌'] = found_brand

    def extract_model_prefix_and_pns(model):
        model = model.replace('/', '-').replace(' ', '').upper()
        m = re.match(r'([A-Z0-9]+-)', model)
        prefix = m.group(1) if m else ''
        pns = set(re.findall(r'(\d+Q)', model))
        return prefix, pns

    def extract_standard_model(s):
        # 匹配如 Z45X-10Q、D341X-16Q、J41X-16Q、Z45X-10Q/16Q 等，归一化为Z45X10Q16Q
        s = str(s).upper().replace(' ', '')
        match = re.search(r'([A-Z0-9]+-?)(\d+[A-Z])((/|-)?\d*[A-Z]*)', s)
        if match:
            prefix = match.group(1).replace('-', '')
            pn1 = match.group(2)
            pn2 = match.group(3).replace('/', '').replace('-', '')
            return f"{prefix}{pn1}{pn2}"
        return s.replace('-', '').replace('/', '')
    
    def extract_standard_model_v2(s):
        # 改进版本：处理包含多个型号的情况，如 "Z45X-10/16Q"
        s = str(s).upper().replace(' ', '')
        
        # 首先尝试匹配包含多个型号的情况，如 "Z45X-10/16Q"
        match = re.search(r'([A-Z0-9]+-?)(\d+)(/)(\d+[A-Z])', s)
        if match:
            prefix = match.group(1).replace('-', '')
            pn1 = match.group(2)
            pn2 = match.group(4)
            # 返回第一个型号作为主要型号
            return f"{prefix}{pn1}Q"
        
        # 然后尝试匹配单个型号的情况
        match = re.search(r'([A-Z0-9]+-?)(\d+[A-Z])((/|-)?\d*[A-Z]*)', s)
        if match:
            prefix = match.group(1).replace('-', '')
            pn1 = match.group(2)
            pn2 = match.group(3).replace('/', '').replace('-', '')
            return f"{prefix}{pn1}{pn2}"
        
        # 如果上面的都不匹配，尝试从整个字符串中提取型号部分
        # 查找包含 "Z45X" 或类似模式的部分
        model_patterns = [
            r'Z45X-\d+/\d+[A-Z]',  # Z45X-10/16Q
            r'Z41X-\d+/\d+[A-Z]',  # Z41X-10/16Q
            r'D341X-\d+/\d+[A-Z]', # D341X-10/16Q
            r'Q41X-\d+/\d+[A-Z]',  # Q41X-10/16Q
            r'J41X-\d+/\d+[A-Z]',  # J41X-10/16Q
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, s)
            if match:
                model_part = match.group(0)
                # 提取第一个型号
                first_match = re.search(r'([A-Z0-9]+-?)(\d+)(/)(\d+[A-Z])', model_part)
                if first_match:
                    prefix = first_match.group(1).replace('-', '')
                    pn1 = first_match.group(2)
                    return f"{prefix}{pn1}Q"
        
        return s.replace('-', '').replace('/', '')
    def normalize(s):
        return str(s).replace('/', '').replace('-', '').replace(' ', '').replace('　', '').upper()

    # 3. 价格匹配、品牌等（三字段全等）
    prices = []
    totals = []
    if price_file is not None and os.path.exists(price_file):
        # 根据文件扩展名选择读取方式
        if price_file.endswith('.csv'):
            price_df = pd.read_csv(price_file)
        else:
            price_df = pd.read_excel(price_file)
        print(f"[调试] 价格表列名: {list(price_df.columns)}")
        print(f"[调试] 价格表前3行数据:")
        print(price_df.head(3))
        
        # 标准化价格表列名
        if '型号' in price_df.columns:
            print(f"[调试] 开始标准化价格表型号...")
            price_df['标准型号'] = price_df['型号'].apply(extract_standard_model_v2)
            print(f"[调试] 价格表型号标准化完成，前5个结果:")
            for i in range(min(5, len(price_df))):
                original = price_df.iloc[i]['型号']
                standardized = price_df.iloc[i]['标准型号']
                print(f"  {original} -> {standardized}")
        elif '标准型号' not in price_df.columns:
            price_df['标准型号'] = ''
            
        # 查找价格列
        price_col = None
        for col in price_df.columns:
            if '价格' in str(col) or '单价' in str(col):
                price_col = col
                print(f"[调试] 找到价格列: {col}")
                break
        if price_col is None:
            # 如果没有找到价格列，尝试其他可能的列名
            for col in price_df.columns:
                if any(keyword in str(col) for keyword in ['价', '元', '金额']):
                    price_col = col
                    print(f"[调试] 找到备选价格列: {col}")
                    break
        
        if not price_col:
            print("[警告] 未找到价格列，跳过价格匹配")
            prices = [''] * len(df)
            totals = [''] * len(df)
        else:
            print(f"[调试] 使用价格列: {price_col}")
            
            for i in range(len(df)):
                std_model = normalize(str(df.iloc[i].get('标准型号', '')).strip())
                spec = normalize(str(df.iloc[i].get('规格型号', '')).strip())
                brand = normalize(str(df.iloc[i].get('品牌', '')).strip())
                qty = df.iloc[i].get('数量', '')
                
                print(f"[调试] 行{i+1}: 原始标准型号='{df.iloc[i].get('标准型号', '')}' -> 标准化后='{std_model}'")
                print(f"[调试] 行{i+1}: 原始规格型号='{df.iloc[i].get('规格型号', '')}' -> 标准化后='{spec}'")
                print(f"[调试] 行{i+1}: 原始品牌='{df.iloc[i].get('品牌', '')}' -> 标准化后='{brand}'")
                
                # 三条件匹配逻辑：品牌、标准型号、规格型号都必须匹配
                matched_price = ''
                
                # 检查价格表是否有品牌列
                brand_col = None
                for col in price_df.columns:
                    if '品牌' in str(col):
                        brand_col = col
                        break
                
                # 检查价格表是否有规格列
                spec_col = None
                for col in price_df.columns:
                    if '规格' in str(col):
                        spec_col = col
                        break
                
                print(f"[调试] 价格表列名: {list(price_df.columns)}")
                print(f"[调试] 找到的品牌列: {brand_col}")
                print(f"[调试] 找到的规格列: {spec_col}")
                print(f"[调试] 价格表前3行数据:")
                print(price_df.head(3))
                
                # 严格三条件匹配：品牌+标准型号+规格型号必须都匹配
                if brand and std_model and spec and brand_col and spec_col:
                    print(f"[调试] 开始三条件匹配:")
                    print(f"  询价表: 品牌='{brand}', 标准型号='{std_model}', 规格型号='{spec}'")
                    
                    # 分别检查每个条件
                    brand_matches = price_df[price_df[brand_col].apply(normalize) == brand]
                    print(f"  品牌匹配: {len(brand_matches)} 条")
                    
                    model_matches = price_df[price_df['标准型号'].apply(normalize) == std_model]
                    print(f"  型号匹配: {len(model_matches)} 条")
                    
                    spec_matches = price_df[price_df[spec_col].apply(normalize) == spec]
                    print(f"  规格匹配: {len(spec_matches)} 条")
                    
                    # 显示价格表中的一些示例数据
                    print(f"  价格表品牌示例: {price_df[brand_col].head(3).tolist()}")
                    print(f"  价格表型号示例: {price_df['标准型号'].head(3).tolist()}")
                    print(f"  价格表规格示例: {price_df[spec_col].head(3).tolist()}")
                    
                    matches = price_df[
                        (price_df[brand_col].apply(normalize) == brand) &
                        (price_df['标准型号'].apply(normalize) == std_model) &
                        (price_df[spec_col].apply(normalize) == spec)
                    ]
                    if not matches.empty:
                        matched_price = str(matches.iloc[0][price_col])
                        print(f"[调试] 三条件匹配成功: 品牌={brand}, 标准型号={std_model}, 规格型号={spec} -> {matched_price}")
                    else:
                        print(f"[调试] 三条件匹配失败: 品牌={brand}, 标准型号={std_model}, 规格型号={spec}")
                else:
                    print(f"[调试] 缺少匹配条件: 品牌={brand}, 标准型号={std_model}, 规格型号={spec}")
                    print(f"  brand={bool(brand)}, std_model={bool(std_model)}, spec={bool(spec)}, brand_col={bool(brand_col)}, spec_col={bool(spec_col)}")
                
                # 如果三条件不匹配，不输出单价
                if not matched_price:
                    print(f"[调试] 三条件不匹配，不输出单价")
                    matched_price = ''  # 确保为空字符串
                
                # 计算总价
                prices.append(matched_price)
                try:
                    # 检查数量和价格是否有效
                    qty_valid = qty and str(qty).strip() != '' and str(qty).strip() != 'nan'
                    price_valid = matched_price and str(matched_price).strip() != '' and str(matched_price).strip() != 'nan'
                    
                    if price_valid and qty_valid:
                        qty_val = float(qty)
                        price_val = float(matched_price)
                        total_val = price_val * qty_val
                        totals.append(str(total_val))
                        print(f"[调试] 计算总价: {price_val} × {qty_val} = {total_val}")
                    else:
                        totals.append('')
                        if not price_valid:
                            print(f"[调试] 价格无效: '{matched_price}'")
                        if not qty_valid:
                            print(f"[调试] 数量无效: '{qty}'")
                except Exception as e:
                    print(f"[警告] 价格计算失败: 单价={matched_price}, 数量={qty}, 错误={e}")
                    totals.append('')
    else:
        print("[调试] 没有价格文件，尝试从原始数据提取价格")
        prices = []
        totals = []
        
        for i in range(len(df)):
            qty = df.iloc[i].get('数量', '')
            price = df.iloc[i].get('单价', '')
            
            # 如果单价列没有数据，尝试从其他列提取价格
            if not price:
                for col in df.columns:
                    if '价格' in str(col) or '单价' in str(col):
                        cell_value = df.iloc[i].get(col, '')
                        if cell_value and str(cell_value).strip() != '':
                            price = str(cell_value).strip()
                            print(f"[调试] 从列 {col} 提取到价格: {price}")
                            break
            
            try:
                if price and qty:
                    qty_val = float(qty)
                    price_val = float(price)
                    total_val = price_val * qty_val
                    totals.append(str(total_val))
                    prices.append(price)  # 同时设置单价
                    print(f"[调试] 计算总价: {price_val} × {qty_val} = {total_val}")
                else:
                    # 如果没有找到价格，不添加任何内容
                    prices.append('')
                    totals.append('')
            except Exception as e:
                print(f"[警告] 价格计算失败: 单价={price}, 数量={qty}, 错误={e}")
                prices.append('')
                totals.append('')
    # 4. 保留原始表头，追加新列到原表最后
    # 确保所有必需的列都存在，但不删除原始列
    if '规格型号' not in df.columns:
        df['规格型号'] = ''
    
    # 确保标准型号列存在
    if '标准型号' not in df.columns:
        df['标准型号'] = models
    
    # 确保品牌列存在
    if '品牌' not in df.columns:
        df['品牌'] = ''
    
    # 确保价格和总价数组长度正确
    if len(prices) != len(df):
        print(f"[警告] 价格数组长度不匹配: {len(prices)} vs {len(df)}")
        if len(prices) > len(df):
            prices = prices[:len(df)]
        else:
            # 不填充空字符串，保持原数组长度
            print(f"[调试] 价格数组长度不足，不填充空值")
    
    if len(totals) != len(df):
        print(f"[警告] 总价数组长度不匹配: {len(totals)} vs {len(df)}")
        if len(totals) > len(df):
            totals = totals[:len(df)]
        else:
            # 不填充空字符串，保持原数组长度
            print(f"[调试] 总价数组长度不足，不填充空值")
    
    # 添加或更新单价和总价列，保留原始列
    df['单价'] = prices
    df['总价'] = totals
    
    # 验证计算结果
    print(f"[验证] 检查前5行的价格计算:")
    for i in range(min(5, len(df))):
        price = df.iloc[i].get('单价', '')
        qty = df.iloc[i].get('数量', '')
        total = df.iloc[i].get('总价', '')
        if price and qty and total:
            try:
                expected_total = float(price) * float(qty)
                actual_total = float(total)
                if abs(expected_total - actual_total) > 0.01:
                    print(f"[错误] 行{i+1}: 期望总价={expected_total}, 实际总价={actual_total}")
                else:
                    print(f"[正确] 行{i+1}: {price} × {qty} = {total}")
            except Exception as e:
                print(f"[错误] 行{i+1}: 价格验证失败 - {e}")
    
    # 调试输出
    print(f"[调试] 最终价格数组: {prices}")
    print(f"[调试] 最终总价数组: {totals}")
    print(f"[调试] 非空价格数量: {sum(1 for p in prices if p)}")
    print(f"[调试] 非空总价数量: {sum(1 for t in totals if t)}")
    # 5. 输出到报价单文件夹
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(input_file)), '报价单')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成CSV文件（品牌列显示为选择的品牌）
    csv_output_file = os.path.join(output_dir, f"{timestamp}_{base_name}_标准格式.csv")
    df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
    print(f"CSV转换完成: {csv_output_file}")
    
    # 生成XLSX文件（保留原始表头）
    xlsx_output_file = os.path.join(output_dir, f"{timestamp}_{base_name}_标准格式.xlsx")
    
    # 创建用于XLSX的DataFrame副本，保留所有原始列
    xlsx_df = df.copy()
    
    # 根据价格匹配结果，确保XLSX文件中的单价列正确显示
    # 如果prices数组中有空值，说明该行没有匹配到价格
    print(f"[DEBUG] XLSX文件价格处理: 总行数={len(xlsx_df)}, 价格数组长度={len(prices)}")
    print(f"[DEBUG] 保留的原始列: {list(xlsx_df.columns)}")
    print(f"[DEBUG] prices数组内容: {prices}")
    print(f"[DEBUG] totals数组内容: {totals}")
    
    for i in range(len(xlsx_df)):
        if i < len(prices):
            matched_price = prices[i]
            matched_total = totals[i] if i < len(totals) else ''
            
            # 检查是否匹配到价格
            if matched_price and str(matched_price).strip() != '' and str(matched_price).strip() != 'nan':
                # 匹配成功，输出价格
                xlsx_df.at[i, '单价'] = matched_price
                xlsx_df.at[i, '总价'] = matched_total if matched_total else ''
                print(f"[DEBUG] 行{i+1}: 匹配成功，输出价格='{matched_price}', 总价='{matched_total}'")
            else:
                # 匹配失败，设置为空
                xlsx_df.at[i, '单价'] = ''
                xlsx_df.at[i, '总价'] = ''
                print(f"[DEBUG] 行{i+1}: 匹配失败，设置为空")
        else:
            # 超出数组范围，设置为空
            xlsx_df.at[i, '单价'] = ''
            xlsx_df.at[i, '总价'] = ''
            print(f"[DEBUG] 行{i+1}: 超出数组范围，设置为空")
    
    xlsx_df.to_excel(xlsx_output_file, index=False, engine='openpyxl')
    print(f"XLSX转换完成: {xlsx_output_file}")
    print(f"[DEBUG] 文件是否存在: CSV={os.path.exists(csv_output_file)}, XLSX={os.path.exists(xlsx_output_file)}")
    # 自动清理历史中间文件，只保留最新的报价表
    # csv_pattern = os.path.join(output_dir, f"*{base_name}_标准格式.csv")
    # xlsx_pattern = os.path.join(output_dir, f"*{base_name}_标准格式.xlsx")
    # all_files = sorted(glob.glob(csv_pattern) + glob.glob(xlsx_pattern), key=lambda x: os.path.getmtime(x), reverse=True)
    # keep_files = set([output_file, output_file.replace('.csv', '.xlsx')])
    # for f in all_files:
    #     if f not in keep_files:
    #         try:
    #             os.remove(f)
    #             print(f"[清理] 已删除历史文件: {f}")
    #         except Exception as e:
    #             print(f"[清理] 删除文件失败: {f}, 错误: {e}")
    return csv_output_file, xlsx_output_file

def batch_process_all_users():
    merchant_root = "merchant_data"
    if not os.path.exists(merchant_root):
        print(f"目录不存在: {merchant_root}")
        return
    for user in os.listdir(merchant_root):
        user_dir = os.path.join(merchant_root, user)
        if not os.path.isdir(user_dir):
            continue
        input_dir = os.path.join(user_dir, "询价表")
        output_dir = os.path.join(user_dir, "报价单")
        price_dir = os.path.join(user_dir, "价格表")
        os.makedirs(output_dir, exist_ok=True)
        excel_files = glob.glob(os.path.join(input_dir, "*.xlsx")) + glob.glob(os.path.join(input_dir, "*.xls"))
        # 自动查找价格表（优先用第一个Excel文件）
        price_file = None
        if os.path.exists(price_dir):
            price_files = glob.glob(os.path.join(price_dir, "*.xlsx")) + glob.glob(os.path.join(price_dir, "*.xls"))
            if price_files:
                price_file = price_files[0]
        if not excel_files:
            print(f"用户 {user} 没有需要处理的Excel文件。")
            continue
        print(f"用户 {user} 询价表文件数: {len(excel_files)}，价格表: {os.path.basename(price_file) if price_file else '无'}")
        for file in excel_files:
            base_name = os.path.splitext(os.path.basename(file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_标准格式.csv")
            process_excel_to_standard_csv(file, output_file, price_file=price_file)

def main():
    batch_process_all_users()

if __name__ == "__main__":
    main()