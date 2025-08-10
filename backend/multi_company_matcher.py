"""
多公司匹配引擎 - 并行处理多个公司的产品匹配
"""
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from multi_company_models import PriceTableInfo, PriceMatch, AggregatedPriceInfo, MultiCompanyQuoteResult

class MultiCompanyMatcher:
    """多公司匹配引擎"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        
    def match_products_multi_company(
        self, 
        inquiry_data: pd.DataFrame, 
        price_tables: List[PriceTableInfo]
    ) -> MultiCompanyQuoteResult:
        """对多个公司执行产品匹配"""
        start_time = time.time()
        
        print(f"🚀 [MATCHER] 开始多公司产品匹配")
        print(f"📋 [MATCHER] 询价产品数量: {len(inquiry_data)}")
        print(f"🏢 [MATCHER] 价格表数量: {len(price_tables)}")
        
        # 过滤有效的价格表
        valid_price_tables = [pt for pt in price_tables if pt.is_valid and pt.data is not None]
        print(f"✅ [MATCHER] 有效价格表数量: {len(valid_price_tables)}")
        
        if not valid_price_tables:
            return MultiCompanyQuoteResult(
                aggregated_prices=[],
                total_companies=0,
                total_products=len(inquiry_data),
                matched_products=0,
                processing_time=time.time() - start_time,
                errors=["没有有效的价格表文件"]
            )
        
        # 并行处理多个公司的匹配
        all_matches = {}
        errors = []
        warnings = []
        
        try:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(valid_price_tables))) as executor:
                # 提交所有匹配任务
                future_to_company = {
                    executor.submit(self.match_single_company, inquiry_data, price_table): price_table.company_name
                    for price_table in valid_price_tables
                }
                
                # 收集结果
                for future in as_completed(future_to_company):
                    company_name = future_to_company[future]
                    try:
                        matches = future.result()
                        all_matches[company_name] = matches
                        print(f"✅ [MATCHER] {company_name} 匹配完成: {len(matches)} 个产品")
                    except Exception as e:
                        error_msg = f"{company_name} 匹配失败: {str(e)}"
                        errors.append(error_msg)
                        print(f"❌ [MATCHER] {error_msg}")
        
        except Exception as e:
            error_msg = f"并行匹配过程出错: {str(e)}"
            errors.append(error_msg)
            print(f"❌ [MATCHER] {error_msg}")
        
        # 聚合匹配结果
        aggregated_prices = self._aggregate_matches(inquiry_data, all_matches)
        
        # 统计结果
        matched_products = sum(1 for price_info in aggregated_prices if price_info.match_count > 0)
        processing_time = time.time() - start_time
        
        result = MultiCompanyQuoteResult(
            aggregated_prices=aggregated_prices,
            total_companies=len(valid_price_tables),
            total_products=len(inquiry_data),
            matched_products=matched_products,
            processing_time=processing_time,
            errors=errors,
            warnings=warnings
        )
        
        print(f"🎉 [MATCHER] 多公司匹配完成: {result.summary}")
        print(f"⏱️ [MATCHER] 处理时间: {processing_time:.2f}秒")
        
        return result
    
    def match_single_company(
        self, 
        inquiry_data: pd.DataFrame, 
        price_table: PriceTableInfo
    ) -> List[PriceMatch]:
        """对单个公司执行产品匹配"""
        matches = []
        
        if not price_table.is_valid or price_table.data is None:
            return matches
        
        price_df = price_table.data
        company_name = price_table.company_name
        
        print(f"🔍 [MATCHER] 开始匹配 {company_name}")
        
        for idx, inquiry_row in inquiry_data.iterrows():
            # 跳过合计行和空行
            if pd.isna(inquiry_row.get('品名')) or str(inquiry_row.get('品名')).strip() in ['合计', '']:
                continue
            
            product_name = str(inquiry_row.get('品名', '')).strip()
            specification = str(inquiry_row.get('规格型号', '')).strip()
            
            if not product_name:
                continue
            
            # 在价格表中查找匹配
            match = self._find_best_match(product_name, specification, price_df, company_name)
            if match:
                matches.append(match)
        
        print(f"✅ [MATCHER] {company_name} 匹配结果: {len(matches)} 个产品")
        return matches
    
    def _find_best_match(
        self, 
        product_name: str, 
        specification: str, 
        price_df: pd.DataFrame, 
        company_name: str
    ) -> Optional[PriceMatch]:
        """在价格表中查找最佳匹配"""
        best_match = None
        best_score = 0
        
        for idx, price_row in price_df.iterrows():
            try:
                # 获取价格表中的产品信息
                price_model = str(price_row.get('型号', '')).strip()
                price_spec = str(price_row.get('规格', '')).strip()
                price_value = price_row.get('价格', 0)
                brand = str(price_row.get('品牌', '')).strip()
                
                # 跳过无效数据
                if not price_model or pd.isna(price_value) or price_value <= 0:
                    continue
                
                # 计算匹配分数
                score = self._calculate_match_score(
                    product_name, specification, 
                    price_model, price_spec
                )
                
                if score > best_score and score >= 0.6:  # 最低匹配阈值
                    best_score = score
                    best_match = PriceMatch(
                        product_name=product_name,
                        specification=specification,
                        company_name=company_name,
                        price=float(price_value),
                        brand=brand,
                        match_confidence=score,
                        original_row=price_row.to_dict()
                    )
            
            except Exception as e:
                # 跳过有问题的行
                continue
        
        return best_match
    
    def _calculate_match_score(
        self, 
        inquiry_name: str, 
        inquiry_spec: str,
        price_model: str, 
        price_spec: str
    ) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 产品名称匹配 (权重 0.4)
        name_score = self._text_similarity(inquiry_name, price_model)
        score += name_score * 0.4
        
        # 规格匹配 (权重 0.6)
        spec_score = self._specification_similarity(inquiry_spec, price_spec)
        score += spec_score * 0.6
        
        return min(score, 1.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # 完全匹配
        if text1 == text2:
            return 1.0
        
        # 包含关系
        if text1 in text2 or text2 in text1:
            return 0.8
        
        # 关键词匹配
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union)
        
        return 0.0
    
    def _specification_similarity(self, spec1: str, spec2: str) -> float:
        """计算规格相似度"""
        if not spec1 or not spec2:
            return 0.0
        
        spec1 = spec1.upper().strip()
        spec2 = spec2.upper().strip()
        
        # 完全匹配
        if spec1 == spec2:
            return 1.0
        
        # 提取DN值进行比较
        dn1 = self._extract_dn_value(spec1)
        dn2 = self._extract_dn_value(spec2)
        
        if dn1 and dn2:
            if dn1 == dn2:
                return 0.9  # DN值匹配给高分
            else:
                return 0.3  # DN值不匹配给低分
        
        # 文本相似度
        return self._text_similarity(spec1, spec2)
    
    def _extract_dn_value(self, text: str) -> Optional[str]:
        """提取DN值"""
        if not text:
            return None
        
        # 匹配DN后面的数字
        patterns = [
            r'DN\s*(\d+)',
            r'φ\s*(\d+)',
            r'Φ\s*(\d+)',
            r'∅\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _aggregate_matches(
        self, 
        inquiry_data: pd.DataFrame, 
        all_matches: Dict[str, List[PriceMatch]]
    ) -> List[AggregatedPriceInfo]:
        """聚合匹配结果"""
        aggregated_prices = []
        
        for idx, inquiry_row in inquiry_data.iterrows():
            # 跳过合计行和空行
            if pd.isna(inquiry_row.get('品名')) or str(inquiry_row.get('品名')).strip() in ['合计', '']:
                continue
            
            product_name = str(inquiry_row.get('品名', '')).strip()
            specification = str(inquiry_row.get('规格型号', '')).strip()
            quantity = str(inquiry_row.get('数量', '')).strip()
            
            if not product_name:
                continue
            
            # 收集该产品在所有公司的匹配结果
            company_prices = {}
            
            for company_name, matches in all_matches.items():
                for match in matches:
                    if (match.product_name == product_name and 
                        match.specification == specification):
                        company_prices[company_name] = match
                        break
            
            # 创建聚合价格信息
            aggregated_info = AggregatedPriceInfo(
                product_name=product_name,
                specification=specification,
                quantity=quantity,
                company_prices=company_prices
            )
            
            aggregated_prices.append(aggregated_info)
        
        return aggregated_prices