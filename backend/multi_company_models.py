"""
多公司价格匹配功能的数据模型定义
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd

@dataclass
class PriceTableInfo:
    """价格表信息"""
    file_path: str
    company_name: str
    file_format: str  # 'xlsx', 'csv'
    is_valid: bool
    data: Optional[pd.DataFrame] = None
    error_message: Optional[str] = None

@dataclass
class PriceMatch:
    """单个产品的价格匹配结果"""
    product_name: str
    specification: str
    company_name: str
    price: float
    brand: str = ""
    match_confidence: float = 1.0
    original_row: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """数据验证"""
        if self.price < 0:
            raise ValueError(f"价格不能为负数: {self.price}")
        if not self.product_name.strip():
            raise ValueError("产品名称不能为空")

@dataclass
class AggregatedPriceInfo:
    """聚合的价格信息"""
    product_name: str
    specification: str
    quantity: str
    company_prices: Dict[str, PriceMatch] = field(default_factory=dict)  # company_name -> PriceMatch
    min_price: float = 0.0
    max_price: float = 0.0
    avg_price: float = 0.0
    best_company: str = ""
    price_range: str = ""
    match_count: int = 0
    
    def __post_init__(self):
        """自动计算统计信息"""
        if self.company_prices:
            prices = [match.price for match in self.company_prices.values()]
            self.min_price = min(prices)
            self.max_price = max(prices)
            self.avg_price = sum(prices) / len(prices)
            self.match_count = len(prices)
            
            # 找到最低价格的公司
            for company, match in self.company_prices.items():
                if match.price == self.min_price:
                    self.best_company = company
                    break
            
            # 设置价格范围描述
            if self.min_price == self.max_price:
                self.price_range = f"¥{self.min_price:.2f}"
            else:
                self.price_range = f"¥{self.min_price:.2f} - ¥{self.max_price:.2f}"

@dataclass
class PriceStatistics:
    """价格统计信息"""
    min_price: float
    max_price: float
    avg_price: float
    price_count: int
    price_variance: float = 0.0
    
    def __post_init__(self):
        """计算价格方差"""
        if self.price_count > 1:
            # 这里简化处理，实际使用时需要传入价格列表计算方差
            self.price_variance = (self.max_price - self.min_price) ** 2 / 4

@dataclass
class MultiCompanyQuoteResult:
    """多公司报价结果"""
    aggregated_prices: List[AggregatedPriceInfo]
    total_companies: int
    total_products: int
    matched_products: int
    processing_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def match_rate(self) -> float:
        """匹配率"""
        if self.total_products == 0:
            return 0.0
        return self.matched_products / self.total_products
    
    @property
    def summary(self) -> str:
        """结果摘要"""
        return (f"处理了{self.total_companies}家公司的价格表，"
                f"共{self.total_products}个产品，"
                f"成功匹配{self.matched_products}个产品，"
                f"匹配率{self.match_rate:.1%}")