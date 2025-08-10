"""
价格表扫描器 - 自动发现和验证价格表文件
"""
import os
import re
from pathlib import Path
from typing import List, Optional
import pandas as pd
from multi_company_models import PriceTableInfo

class PriceTableScanner:
    """价格表扫描器"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.required_columns = ['型号', '规格', '价格']  # 价格表必须包含的列
        
    def scan_price_tables(self, user_dir: str) -> List[PriceTableInfo]:
        """扫描用户目录下的所有价格表文件"""
        price_tables = []
        price_table_dir = os.path.join(user_dir, "价格表")
        
        print(f"🔍 [SCANNER] 扫描价格表目录: {price_table_dir}")
        
        if not os.path.exists(price_table_dir):
            print(f"⚠️ [SCANNER] 价格表目录不存在: {price_table_dir}")
            return price_tables
        
        try:
            for filename in os.listdir(price_table_dir):
                file_path = os.path.join(price_table_dir, filename)
                
                # 跳过目录和隐藏文件
                if os.path.isdir(file_path) or filename.startswith('.'):
                    continue
                
                # 检查文件格式
                file_ext = Path(filename).suffix.lower()
                if file_ext not in self.supported_formats:
                    print(f"⚠️ [SCANNER] 跳过不支持的文件格式: {filename}")
                    continue
                
                # 提取公司名称
                company_name = self.extract_company_name(filename)
                
                # 验证文件
                is_valid, error_msg = self.validate_price_table(file_path)
                
                price_table = PriceTableInfo(
                    file_path=file_path,
                    company_name=company_name,
                    file_format=file_ext[1:],  # 去掉点号
                    is_valid=is_valid,
                    error_message=error_msg
                )
                
                price_tables.append(price_table)
                
                if is_valid:
                    print(f"✅ [SCANNER] 发现有效价格表: {company_name} ({filename})")
                else:
                    print(f"❌ [SCANNER] 发现无效价格表: {company_name} ({filename}) - {error_msg}")
                    
        except Exception as e:
            print(f"❌ [SCANNER] 扫描价格表目录时出错: {e}")
        
        print(f"📊 [SCANNER] 扫描完成，共发现 {len(price_tables)} 个价格表文件")
        return price_tables
    
    def extract_company_name(self, filename: str) -> str:
        """从文件名提取公司名称"""
        # 去掉文件扩展名
        name_without_ext = Path(filename).stem
        
        # 常见的公司名提取规则
        patterns = [
            r'^(.+?)[-_\s]*价格表?$',  # "公司A-价格表.xlsx" -> "公司A"
            r'^(.+?)[-_\s]*报价表?$',  # "公司B_报价表.xlsx" -> "公司B"  
            r'^(.+?)[-_\s]*价格$',     # "公司C 价格.xlsx" -> "公司C"
            r'^(.+?)[-_\s]*报价$',     # "公司D-报价.xlsx" -> "公司D"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if company_name:
                    return company_name
        
        # 如果没有匹配到特定模式，直接使用文件名（去掉扩展名）
        return name_without_ext
    
    def validate_price_table(self, file_path: str) -> tuple[bool, Optional[str]]:
        """验证价格表文件的有效性"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "文件为空"
            
            if file_size > 50 * 1024 * 1024:  # 50MB限制
                return False, "文件过大（超过50MB）"
            
            # 尝试读取文件
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path, nrows=5)  # 只读取前5行进行验证
                else:
                    df = pd.read_excel(file_path, nrows=5)
                
                if df.empty:
                    return False, "文件内容为空"
                
                # 检查必要的列是否存在
                columns = [str(col).strip() for col in df.columns]
                missing_columns = []
                
                for required_col in self.required_columns:
                    # 模糊匹配列名
                    if not self._find_column_match(required_col, columns):
                        missing_columns.append(required_col)
                
                if missing_columns:
                    return False, f"缺少必要的列: {', '.join(missing_columns)}"
                
                return True, None
                
            except Exception as e:
                return False, f"文件读取失败: {str(e)}"
                
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"
    
    def _find_column_match(self, target_col: str, columns: List[str]) -> bool:
        """模糊匹配列名"""
        target_lower = target_col.lower()
        
        for col in columns:
            col_lower = col.lower()
            if target_lower in col_lower or col_lower in target_lower:
                return True
            
            # 特殊匹配规则
            if target_col == '型号' and any(keyword in col_lower for keyword in ['型号', 'model', '规格型号']):
                return True
            elif target_col == '规格' and any(keyword in col_lower for keyword in ['规格', 'spec', 'dn', '口径']):
                return True
            elif target_col == '价格' and any(keyword in col_lower for keyword in ['价格', 'price', '单价', '报价']):
                return True
        
        return False
    
    def load_price_table_data(self, price_table: PriceTableInfo) -> bool:
        """加载价格表数据到内存"""
        if not price_table.is_valid:
            return False
        
        try:
            if price_table.file_format == 'csv':
                df = pd.read_csv(price_table.file_path)
            else:
                df = pd.read_excel(price_table.file_path)
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            price_table.data = df
            print(f"📊 [SCANNER] 成功加载价格表数据: {price_table.company_name} ({len(df)} 行)")
            return True
            
        except Exception as e:
            price_table.error_message = f"数据加载失败: {str(e)}"
            print(f"❌ [SCANNER] 加载价格表数据失败: {price_table.company_name} - {e}")
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
            # 价格列映射
            elif any(keyword in col_lower for keyword in ['价格', 'price', '单价', '报价']):
                column_mapping[col] = '价格'
            # 品牌列映射
            elif any(keyword in col_lower for keyword in ['品牌', 'brand']):
                column_mapping[col] = '品牌'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        return df