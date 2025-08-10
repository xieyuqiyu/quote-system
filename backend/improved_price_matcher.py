"""
改进的价格匹配器 - 根据价格表中的型号、规格、品牌、价格来匹配产品并生成总价
"""
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from csv_utils import safe_read_csv, safe_to_csv

class ImprovedPriceMatcher:
    """改进的价格匹配器"""
    
    def __init__(self):
        self.price_df = None
        self.brand_columns = []
        
    def load_price_table(self, price_file_path: str) -> bool:
        """加载价格表，支持 .csv / .xlsx / .xls"""
        try:
            file_lower = str(price_file_path).lower()
            if file_lower.endswith((".xlsx", ".xls")):
                # 直接读取Excel
                self.price_df = pd.read_excel(price_file_path, engine="openpyxl")
            else:
                # 默认按CSV读取（含自动编码探测）
                self.price_df = safe_read_csv(price_file_path)

            print(f"📊 [MATCHER] 成功加载价格表: {len(self.price_df)} 行数据")
            print(f"📋 [MATCHER] 价格表列名: {list(self.price_df.columns)}")

            # 标准化列名
            self.price_df = self._standardize_columns(self.price_df)

            # 识别品牌列
            self._identify_brand_columns()

            return True
        except Exception as e:
            print(f"❌ [MATCHER] 加载价格表失败: {e}")
            return False
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {}
        
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            
            # 型号列映射
            if any(keyword in col_lower for keyword in ['型号', 'model']):
                column_mapping[col] = '型号'
            # 规格列映射
            elif any(keyword in col_lower for keyword in ['规格', 'spec', 'dn', '口径']):
                column_mapping[col] = '规格'
            # 品牌列映射
            elif any(keyword in col_lower for keyword in ['品牌', 'brand']):
                column_mapping[col] = '品牌'
            # 价格列映射
            elif any(keyword in col_lower for keyword in ['价格', 'price', '单价', '报价']):
                column_mapping[col] = '价格'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            print(f"📋 [MATCHER] 列名映射: {column_mapping}")
        
        return df
    
    def _identify_brand_columns(self):
        """识别品牌相关的列"""
        self.brand_columns = []
        
        # 检查是否有单独的品牌列
        if '品牌' in self.price_df.columns:
            unique_brands = self.price_df['品牌'].dropna().unique()
            self.brand_columns = [f"{brand}" for brand in unique_brands if brand]
            print(f"🏷️ [MATCHER] 发现品牌: {unique_brands}")
        
        # 检查是否有以品牌名命名的价格列
        brand_keywords = ['上海沪工', '上海良工', '中核苏阀', '上海泰科', '上海科尼特', '上海科尼菲']
        for col in self.price_df.columns:
            for brand in brand_keywords:
                if brand in str(col):
                    if brand not in self.brand_columns:
                        self.brand_columns.append(brand)
        
        print(f"🏷️ [MATCHER] 识别到的品牌列: {self.brand_columns}")
    
    def match_product(self, product_name: str, specification: str, model_code: str = "", selected_brand: Optional[str] = None) -> Dict:
        """匹配单个产品（三匹配优先：型号+名称+品牌，其次回退到原有策略）"""
        if self.price_df is None:
            return {"success": False, "error": "价格表未加载"}
        
        print(f"\n🔍 [MATCHER] 开始匹配产品:")
        print(f"   品名: '{product_name}'")
        print(f"   规格: '{specification}'")
        print(f"   型号: '{model_code}'")
        if selected_brand:
            print(f"   指定品牌: '{selected_brand}'")
        
        # 提取DN值
        dn_value = self._extract_dn_value(specification)
        print(f"   提取的DN值: '{dn_value}'")
        # 优先：三匹配评分（型号+名称+品牌），并在有DN时限定规格
        tri_result = self._tri_match(product_name, model_code, selected_brand, dn_value)
        if tri_result:
            print(f"✅ [MATCHER] 三匹配命中")
            return {"success": True, "matches": [tri_result], "best_match": tri_result}

        # 回退：原有多策略匹配
        matches = []
        if model_code:
            matches.extend(self._match_by_model(model_code, dn_value))
        if dn_value:
            matches.extend(self._match_by_specification(dn_value))
        matches.extend(self._match_by_product_name(product_name, dn_value))
        matches = self._deduplicate_matches(matches)
        if matches:
            print(f"✅ [MATCHER] 回退策略命中 {len(matches)} 项")
            return {"success": True, "matches": matches, "best_match": matches[0]}
        print(f"❌ [MATCHER] 未找到匹配项")
        return {"success": False, "error": "未找到匹配的产品"}

    def _tri_match(self, product_name: str, model_code: str, selected_brand: Optional[str], dn_value: str) -> Optional[Dict]:
        import re
        def normalize(s: Optional[str]) -> str:
            if pd.isna(s) or s is None:
                return ""
            return re.sub(r"\s+", "", str(s)).lower()

        # 识别列
        model_col = '型号' if '型号' in self.price_df.columns else None
        name_col = None
        for c in ['产品名称', '品名', '名称', '项目名称', '物料名称']:
            if c in self.price_df.columns:
                name_col = c
                break
        brand_col = '品牌' if '品牌' in self.price_df.columns else None
        spec_col = '规格' if '规格' in self.price_df.columns else None

        q_model = normalize(model_code)
        q_name = normalize(product_name)
        q_brand = normalize(selected_brand) if selected_brand else ''

        # 候选集（按品牌过滤）
        price_rows = self.price_df
        if q_brand and brand_col:
            price_rows = price_rows[price_rows[brand_col].apply(lambda x: normalize(x) == q_brand)]

        # 规格限定（有DN时约束）
        if dn_value and spec_col:
            dn_num = dn_value.replace('DN', '')
            price_rows = price_rows[price_rows[spec_col].astype(str).str.contains(dn_num, case=False, na=False)]

        best_score = 0
        best_row = None
        for _, prow in price_rows.iterrows():
            p_model = normalize(prow.get(model_col, '')) if model_col else ''
            p_name = normalize(prow.get(name_col, '')) if name_col else ''
            p_brand = normalize(prow.get(brand_col, '')) if brand_col else ''
            score = 0
            # 型号
            if q_model and p_model and q_model == p_model:
                score += 10
            elif q_model and p_model and (q_model in p_model or p_model in q_model):
                score += 6
            # 名称
            if q_name and p_name and q_name == p_name:
                score += 5
            elif q_name and p_name and (q_name in p_name or p_name in q_name):
                score += 3
            # 品牌
            if q_brand and p_brand and q_brand == p_brand:
                score += 2
            elif q_brand and p_brand and (q_brand in p_brand or p_brand in q_brand):
                score += 1

            if score > best_score:
                best_score = score
                best_row = prow

        if best_row is not None and best_score > 0:
            return self._create_match_info(best_row, "三匹配", 0.95 if best_score >= 15 else 0.8)
        return None
    
    def _extract_dn_value(self, specification: str) -> str:
        """提取DN值"""
        if pd.isna(specification) or not specification:
            return ""
        
        spec_str = str(specification).upper()
        
        # 匹配DN后面的数字
        patterns = [
            r'DN\s*(\d+)',
            r'φ\s*(\d+)',
            r'Φ\s*(\d+)',
            r'∅\s*(\d+)',
            r'直径\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spec_str)
            if match:
                return f"DN{match.group(1)}"
        
        # 如果没有找到DN，尝试提取纯数字
        numbers = re.findall(r'\d+', spec_str)
        if numbers:
            # 取第一个数字作为DN值
            return f"DN{numbers[0]}"
        
        return ""
    
    def _match_by_model(self, model_code: str, dn_value: str) -> List[Dict]:
        """根据型号匹配"""
        matches = []
        
        if not model_code:
            return matches
        
        model_code = str(model_code).strip()
        
        # 精确匹配
        exact_matches = self.price_df[
            self.price_df['型号'].str.contains(model_code, case=False, na=False)
        ]
        
        if dn_value:
            exact_matches = exact_matches[
                exact_matches['规格'].str.contains(dn_value.replace('DN', ''), case=False, na=False)
            ]
        
        for _, row in exact_matches.iterrows():
            match_info = self._create_match_info(row, "型号精确匹配", 0.9)
            matches.append(match_info)
        
        return matches
    
    def _match_by_specification(self, dn_value: str) -> List[Dict]:
        """根据规格匹配"""
        matches = []
        
        if not dn_value:
            return matches
        
        dn_number = dn_value.replace('DN', '')
        
        # 匹配规格列中包含相同DN值的记录
        spec_matches = self.price_df[
            self.price_df['规格'].str.contains(dn_number, case=False, na=False)
        ]
        
        for _, row in spec_matches.iterrows():
            match_info = self._create_match_info(row, "规格匹配", 0.7)
            matches.append(match_info)
        
        return matches
    
    def _match_by_product_name(self, product_name: str, dn_value: str) -> List[Dict]:
        """根据产品名称模糊匹配"""
        matches = []
        
        if not product_name:
            return matches
        
        # 提取产品名称中的关键词
        keywords = self._extract_product_keywords(product_name)
        
        for keyword in keywords:
            if len(keyword) >= 2:  # 只考虑长度>=2的关键词
                keyword_matches = self.price_df[
                    self.price_df['型号'].str.contains(keyword, case=False, na=False)
                ]
                
                if dn_value:
                    dn_number = dn_value.replace('DN', '')
                    keyword_matches = keyword_matches[
                        keyword_matches['规格'].str.contains(dn_number, case=False, na=False)
                    ]
                
                for _, row in keyword_matches.iterrows():
                    match_info = self._create_match_info(row, f"关键词匹配({keyword})", 0.5)
                    matches.append(match_info)
        
        return matches
    
    def _extract_product_keywords(self, product_name: str) -> List[str]:
        """从产品名称中提取关键词"""
        if not product_name:
            return []
        
        # 常见的阀门类型关键词
        valve_types = [
            '球阀', '闸阀', '截止阀', '止回阀', '蝶阀', '调节阀', '安全阀', '减压阀',
            '电磁阀', '针型阀', '隔膜阀', '旋塞阀', '柱塞阀', '排气阀', '排泥阀'
        ]
        
        keywords = []
        product_name_str = str(product_name)
        
        # 提取阀门类型
        for valve_type in valve_types:
            if valve_type in product_name_str:
                keywords.append(valve_type)
        
        # 提取型号相关的字母数字组合
        model_patterns = re.findall(r'[A-Z]+\d*[A-Z]*', product_name_str.upper())
        keywords.extend(model_patterns)
        
        return keywords
    
    def _create_match_info(self, row: pd.Series, match_type: str, confidence: float) -> Dict:
        """创建匹配信息"""
        match_info = {
            "型号": str(row.get('型号', '')),
            "规格": str(row.get('规格', '')),
            "品牌": str(row.get('品牌', '')),
            "价格": self._extract_price(row),
            "匹配类型": match_type,
            "置信度": confidence,
            "原始数据": row.to_dict()
        }
        
        return match_info
    
    def _extract_price(self, row: pd.Series) -> float:
        """提取价格"""
        # 首先尝试从价格列获取
        if '价格' in row and not pd.isna(row['价格']):
            try:
                return float(row['价格'])
            except (ValueError, TypeError):
                pass
        
        # 尝试从其他可能的价格列获取
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in ['价格', 'price', '单价', '报价']):
                try:
                    if not pd.isna(row[col]):
                        return float(row[col])
                except (ValueError, TypeError):
                    continue
        
        return 0.0
    
    def _deduplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """去重并按置信度排序"""
        if not matches:
            return []
        
        # 按型号+规格去重
        seen = set()
        unique_matches = []
        
        for match in matches:
            key = (match['型号'], match['规格'], match['品牌'])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        # 按置信度降序排序
        unique_matches.sort(key=lambda x: x['置信度'], reverse=True)
        
        return unique_matches
    
    def process_inquiry_with_totals(self, inquiry_df: pd.DataFrame) -> pd.DataFrame:
        """处理询价表并计算总价"""
        print(f"📊 [MATCHER] 开始处理询价表: {len(inquiry_df)} 行数据")
        
        # 添加匹配结果列
        inquiry_df['匹配型号'] = ''
        inquiry_df['匹配规格'] = ''
        inquiry_df['匹配品牌'] = ''
        inquiry_df['匹配价格'] = 0.0
        inquiry_df['单价'] = 0.0
        inquiry_df['总价'] = 0.0
        inquiry_df['匹配状态'] = ''
        
        for idx, row in inquiry_df.iterrows():
            # 跳过合计行
            if pd.isna(row.get('品名')) or str(row.get('品名')).strip() in ['合计', '总计', '']:
                continue
            
            product_name = str(row.get('品名', ''))
            specification = str(row.get('规格型号', ''))
            model_code = str(row.get('标准型号', ''))
            quantity = row.get('数量', 1)
            
            # 匹配产品
            match_result = self.match_product(product_name, specification, model_code)
            
            if match_result['success']:
                best_match = match_result['best_match']
                
                # 填充匹配信息
                inquiry_df.at[idx, '匹配型号'] = best_match['型号']
                inquiry_df.at[idx, '匹配规格'] = best_match['规格']
                inquiry_df.at[idx, '匹配品牌'] = best_match['品牌']
                inquiry_df.at[idx, '匹配价格'] = best_match['价格']
                inquiry_df.at[idx, '单价'] = best_match['价格']
                inquiry_df.at[idx, '匹配状态'] = f"成功({best_match['匹配类型']})"
                
                # 计算总价
                try:
                    if not pd.isna(quantity) and quantity != '':
                        qty = float(quantity)
                        total_price = best_match['价格'] * qty
                        inquiry_df.at[idx, '总价'] = total_price
                        print(f"✅ [MATCHER] 第{idx+1}行: {product_name} -> {best_match['型号']} (¥{best_match['价格']} × {qty} = ¥{total_price})")
                    else:
                        # 数量为空时，总价设为0
                        inquiry_df.at[idx, '总价'] = 0.0
                        print(f"✅ [MATCHER] 第{idx+1}行: {product_name} -> {best_match['型号']} (¥{best_match['价格']}, 数量为空)")
                except (ValueError, TypeError):
                    # 数量格式错误时，总价设为0
                    inquiry_df.at[idx, '总价'] = 0.0
                    print(f"⚠️ [MATCHER] 第{idx+1}行: 数量格式错误，总价设为0")
            else:
                inquiry_df.at[idx, '匹配状态'] = '未匹配'
                print(f"❌ [MATCHER] 第{idx+1}行: {product_name} -> 未找到匹配")
        
        # 添加合计行
        total_amount = inquiry_df['总价'].sum(skipna=True)
        summary_row = {
            '品名': '合计',
            '总价': total_amount,
            '匹配状态': f'总金额: ¥{total_amount:.2f}'
        }
        
        # 将合计行添加到数据框
        summary_df = pd.DataFrame([summary_row])
        result_df = pd.concat([inquiry_df, summary_df], ignore_index=True)
        
        print(f"💰 [MATCHER] 处理完成，总金额: ¥{total_amount:.2f}")
        
        return result_df