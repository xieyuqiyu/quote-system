from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from datetime import datetime


# -----------------------------
# 数据结构定义
# -----------------------------
@dataclass
class HeaderLayout:
    logo_path: Optional[str] = None
    theme_color: str = "#1F497D"
    font_name: str = "Microsoft YaHei"
    title_align: str = "center"
    content_align: str = "left"
    spacing_rows: int = 1


@dataclass
class QuoteContext:
    customer_id: str
    customer_name: Optional[str] = None
    quote_no: Optional[str] = None
    quote_date: Optional[str] = None
    currency: str = "CNY"
    tax_rate: float = 0.13
    valid_days: int = 30
    lead_time: str = "7-10 天"
    payment_terms: str = "款到发货"
    sales_contact: Optional[str] = None
    sales_phone: Optional[str] = None
    sales_email: Optional[str] = None


@dataclass
class HeaderBlocks:
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class HeaderConfig:
    title_fn: Callable[[QuoteContext], str]
    company_block_fn: Callable[[QuoteContext], List[List[str]]]
    customer_block_fn: Callable[[QuoteContext], List[List[str]]]
    meta_block_fn: Callable[[QuoteContext], List[List[str]]]
    footer_block_fn: Callable[[QuoteContext], List[List[str]]]
    layout: HeaderLayout = field(default_factory=HeaderLayout)


# -----------------------------
# 默认表头函数实现
# -----------------------------

def _default_title(context: QuoteContext) -> str:
    title = "报价单"
    if context.customer_name:
        title = f"{context.customer_name} 报价单"
    return title


def _default_company_block(context: QuoteContext) -> List[List[str]]:
    return [
        ["公司名称", context.customer_name or ""],
        ["业务联系人", context.sales_contact or ""],
        ["联系电话", context.sales_phone or ""],
        ["联系邮箱", context.sales_email or ""],
    ]


def _default_customer_block(context: QuoteContext) -> List[List[str]]:
    return [
        ["客户抬头", context.customer_name or "客户"],
        ["收件人", ""],
        ["联系方式", ""],
        ["地址", ""],
    ]


def _default_meta_block(context: QuoteContext) -> List[List[str]]:
    quote_date = context.quote_date or datetime.now().strftime("%Y-%m-%d")
    quote_no = context.quote_no or datetime.now().strftime("Q%Y%m%d%H%M%S")
    return [
        ["报价编号", quote_no],
        ["报价日期", quote_date],
        ["币种", context.currency],
        ["税率", f"{int(context.tax_rate * 100)}%"],
        ["有效期", f"{context.valid_days} 天"],
        ["交期", context.lead_time],
        ["付款条件", context.payment_terms],
    ]


def _default_footer_block(context: QuoteContext) -> List[List[str]]:
    return [
        ["声明", "此报价为参考价，具体以合同为准。"],
        ["备注", "本报价含税/不含税信息以列明为准。"],
    ]


# -----------------------------
# 构建表头
# -----------------------------

def build_quote_header(config: HeaderConfig, context: QuoteContext) -> HeaderBlocks:
    rows: List[List[str]] = []

    # 标题
    rows.append([config.title_fn(context)])

    # 公司信息块
    rows.append([""])  # 空行
    rows.extend(config.company_block_fn(context))

    # 客户信息块
    rows.append([""])  # 空行
    rows.extend(config.customer_block_fn(context))

    # 元信息块
    rows.append([""])  # 空行
    rows.extend(config.meta_block_fn(context))

    # 备注/声明
    rows.append([""])  # 空行
    rows.extend(config.footer_block_fn(context))

    return HeaderBlocks(rows=rows)


# -----------------------------
# 获取客户配置（可根据customer_id返回不同模板）
# -----------------------------

def get_customer_header_config(customer_id: str) -> HeaderConfig:
    # 在这里可以按customer_id路由不同模板；当前返回默认模板
    return HeaderConfig(
        title_fn=_default_title,
        company_block_fn=_default_company_block,
        customer_block_fn=_default_customer_block,
        meta_block_fn=_default_meta_block,
        footer_block_fn=_default_footer_block,
        layout=HeaderLayout(),
    )


# -----------------------------
# 列映射配置（供识别询价列名用）
# -----------------------------
DEFAULT_COLUMN_ALIASES: Dict[str, List[str]] = {
    "产品名称": ["产品名称", "品名", "名称", "product", "item", "项目名称", "物料名称"],
    "型号": ["型号", "model", "标准型号", "规格型号", "货号", "part no", "型号编码"],
    "规格": ["规格", "dn", "规格型号", "口径", "参数", "尺寸", "spec"],
    "数量": ["数量", "qty", "数量(PCS)", "数量（个）", "数量（件）", "个数", "quantity"],
    "单价": ["单价", "价格", "报价", "含税单价", "未税单价", "price", "unit price"],
    "备注": ["备注", "说明", "note", "备注信息"],
}


def map_columns(header: List[str]) -> Dict[str, Optional[str]]:
    """将表头列名映射到统一字段名称。返回 {标准字段: 实际列名或None}。"""
    header_lower = [str(h).strip().lower() for h in header]
    result: Dict[str, Optional[str]] = {}
    for std_field, aliases in DEFAULT_COLUMN_ALIASES.items():
        match_col = None
        for alias in aliases:
            try_alias = str(alias).strip().lower()
            for idx, col in enumerate(header_lower):
                if try_alias in col:
                    match_col = header[idx]
                    break
            if match_col:
                break
        result[std_field] = match_col
    return result 