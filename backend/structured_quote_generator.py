import os
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import math

from csv_utils import safe_read_csv, safe_to_csv
from improved_price_matcher import ImprovedPriceMatcher
from quote_header_templates import (
    QuoteContext,
    get_customer_header_config,
    build_quote_header,
    map_columns,
)


STANDARD_COLUMNS = ["产品名称(标准)", "型号", "规格", "数量", "单价", "金额", "备注"]


def _normalize_header(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    header = list(df.columns)
    mapping = map_columns(header)

    # 至少要有 型号/规格/数量 中的关键列，以及产品名称或备注用于辅助
    # 如果不存在，则尝试用空列补齐以保持流程
    def ensure_col(col_name: str):
        if mapping.get(col_name) is None:
            # 创建一个空列名以便后续访问
            fake_col = f"__{col_name}__"
            df[fake_col] = ""
            mapping[col_name] = fake_col

    for name in ["产品名称", "型号", "规格", "数量", "单价", "备注"]:
        ensure_col(name)

    return df, mapping


def _prepare_price_matcher(price_file: str) -> ImprovedPriceMatcher:
    matcher = ImprovedPriceMatcher()
    if not matcher.load_price_table(price_file):
        raise RuntimeError("价格表加载失败")
    return matcher


def _match_row(matcher: ImprovedPriceMatcher, product_name: str, spec: str, model: str, selected_brand: Optional[str] = None) -> Optional[Dict]:
    result = matcher.match_product(product_name, spec, model, selected_brand=selected_brand)
    if not result.get("success"):
        return None
    best = result.get("best_match") or {}
    return best


def _extract_price_product_name(best_match: Optional[Dict]) -> Optional[str]:
    """从匹配结果中提取价格表的产品名称（优先使用价格表中的名称列）。"""
    if not best_match:
        return None
    data = best_match.get("原始数据", {}) or {}
    for key in ["产品名称", "品名", "名称", "项目名称", "物料名称"]:
        val = data.get(key)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return None


def _format_number(val: Optional[float], decimals: int = 2) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        f = float(val)
    except Exception:
        return None
    # 过滤 NaN/Inf
    if pd.isna(f) or not math.isfinite(f):
        return None
    try:
        return round(f, decimals)
    except Exception:
        return None


def generate_structured_quote(
    inquiry_path: str,
    price_path: str,
    output_dir: str,
    customer_id: str,
    customer_name: Optional[str] = None,
    selected_brand: Optional[str] = None,
    discount: float = 1.0,
    currency: str = "CNY",
    tax_rate: float = 0.13,
    valid_days: int = 30,
    lead_time: str = "7-10 天",
    payment_terms: str = "款到发货",
    sales_contact: Optional[str] = None,
    sales_phone: Optional[str] = None,
    sales_email: Optional[str] = None,
    company_info: Optional[Dict] = None,
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    # 读取询价表
    if inquiry_path.lower().endswith(".csv"):
        df = safe_read_csv(inquiry_path)
    else:
        df = pd.read_excel(inquiry_path, engine="openpyxl")

    df, mapping = _normalize_header(df)

    # 构建输出明细
    matcher = _prepare_price_matcher(price_path)

    output_rows: List[Dict] = []

    # 如果输入表已包含单价（说明第一种方案已写入匹配结果），直接用这些行构建第二种方案
    has_unit_price_col = "单价" in df.columns
    has_any_unit_price = bool(has_unit_price_col and df["单价"].notna().any())

    if has_any_unit_price:
        for _, row in df.iterrows():
            unit_price_raw = row.get("单价", None)
            if unit_price_raw is None or str(unit_price_raw).strip() == "":
                continue  # 仅保留匹配成功且已有单价的行

            raw_name = str(row.get(mapping["产品名称"], "") or row.get("品名", "") or row.get("名称", "") or "").strip()
            raw_model = str(row.get(mapping["型号"], "") or row.get("标准型号", "") or row.get("规格型号", "") or "").strip()
            raw_spec = str(row.get(mapping["规格"], "") or row.get("规格型号", "") or "").strip()
            raw_qty = row.get(mapping["数量"], row.get("数量", 1))
            raw_remark = str(row.get(mapping["备注"], "") or row.get("备注", "") or "").strip()

            try:
                qty = float(raw_qty) if str(raw_qty).strip() != "" else 0
            except Exception:
                qty = 0
            unit_price = _format_number(unit_price_raw)
            # 仅输出有有效单价的行
            if unit_price is None:
                continue
            # 应用折扣
            if discount is None:
                discount = 1.0
            try:
                unit_price = _format_number(unit_price * float(discount))
            except Exception:
                pass
            amount = _format_number((unit_price or 0) * qty)

            # 为了得到标准产品名称，使用三匹配仅做信息补充（不再依赖其价格）
            best = _match_row(matcher, raw_name, raw_spec, raw_model, selected_brand=selected_brand)
            standard_name = _extract_price_product_name(best) or raw_name

            output_rows.append({
                "产品名称(标准)": standard_name,
                "型号": (best.get("型号") if best else None) or raw_model,
                "规格": (best.get("规格") if best else None) or raw_spec,
                "数量": qty,
                "单价": unit_price,
                "金额": amount,
                "备注": raw_remark,
            })
    else:
        # 正常匹配流程（未提前写入单价的情况）
        for _, row in df.iterrows():
            raw_name = str(row.get(mapping["产品名称"], "") or "").strip()
            raw_model = str(row.get(mapping["型号"], "") or "").strip()
            raw_spec = str(row.get(mapping["规格"], "") or "").strip()
            raw_qty = row.get(mapping["数量"], 1)
            raw_remark = str(row.get(mapping["备注"], "") or "").strip()

            # 清理数量
            try:
                qty = float(raw_qty) if str(raw_qty).strip() != "" else 0
            except Exception:
                qty = 0

            # 匹配价格
            best = _match_row(matcher, raw_name, raw_spec, raw_model, selected_brand=selected_brand)
            if not best:
                # 非我司产品：过滤，不进入主报价
                continue

            unit_price = _format_number(best.get("价格"))
            # 仅输出有有效单价的行
            if unit_price is None:
                continue
            # 应用折扣
            if discount is None:
                discount = 1.0
            try:
                unit_price = _format_number(unit_price * float(discount))
            except Exception:
                pass
            amount = _format_number((unit_price or 0) * qty)

            # 使用价格表标准产品名称（若有）
            standard_name = _extract_price_product_name(best) or raw_name

            output_rows.append({
                "产品名称(标准)": standard_name,
                "型号": best.get("型号") or raw_model,
                "规格": best.get("规格") or raw_spec,
                "数量": qty,
                "单价": unit_price,
                "金额": amount,
                "备注": raw_remark,
            })

    # 若全部为空，给出提示性空单据
    data_df = pd.DataFrame(output_rows, columns=STANDARD_COLUMNS)

    # 汇总
    subtotal = data_df["金额"].sum(skipna=True) if not data_df.empty else 0.0
    
    # 使用用户选择的税率
    user_tax_rate = tax_rate  # 默认使用函数参数
    if company_info and company_info.get("tax_rate") is not None:
        user_tax_rate = company_info.get("tax_rate")
    
    # 根据税率计算税额
    if user_tax_rate == 0.0:
        # 不含税
        tax_amount = 0.0
        total = subtotal
    else:
        # 有税率
        tax_amount = subtotal * user_tax_rate
        total = subtotal + tax_amount

    # 构造表头
    ctx = QuoteContext(
        customer_id=customer_id,
        customer_name=customer_name,
        quote_no=datetime.now().strftime("Q%Y%m%d%H%M%S"),
        quote_date=datetime.now().strftime("%Y-%m-%d"),
        currency=currency,
        tax_rate=user_tax_rate,  # 使用用户选择的税率
        valid_days=valid_days,
        lead_time=lead_time,
        payment_terms=payment_terms,
        sales_contact=sales_contact,
        sales_phone=sales_phone,
        sales_email=sales_email,
    )
    header_cfg = get_customer_header_config(customer_id)
    blocks = build_quote_header(header_cfg, ctx)
    
    # 如果有公司信息，覆盖表头中的公司信息
    if company_info:
        # 创建自定义表头
        custom_blocks = []
        
        # 公司信息块
        company_rows = [
            ["公司名称", company_info.get("company_name", "")],
            ["业务联系人", company_info.get("business_contact", "")],
            ["联系电话", company_info.get("contact_phone", "")],
            ["联系邮箱", company_info.get("contact_email", "")],
        ]
        custom_blocks.extend(company_rows)
        custom_blocks.append([])  # 空行
        
        # 客户信息块
        customer_rows = [
            ["客户抬头", company_info.get("customer_header", "")],
            ["收件人", company_info.get("recipient", "")],
            ["联系方式", company_info.get("contact_method", "")],
            ["地址", company_info.get("address", "")],
        ]
        custom_blocks.extend(customer_rows)
        custom_blocks.append([])  # 空行
        
        # 报价信息块
        quote_rows = [
            ["报价编号", ctx.quote_no],
            ["报价日期", ctx.quote_date],
            ["币种", ctx.currency],
            ["税率", f"{int(user_tax_rate * 100)}%" if user_tax_rate > 0 else "不含税"],
            ["有效期", f"{ctx.valid_days} 天"],
            ["交期", ctx.lead_time],
            ["付款条件", ctx.payment_terms],
        ]
        custom_blocks.extend(quote_rows)
        custom_blocks.append([])  # 空行
        
        # 声明和备注
        custom_blocks.extend([
            ["声明", "此报价为参考价,具体以合同为准。"],
            ["备注", "本报价含税/不含税信息以列明为准。"],
        ])
        custom_blocks.append([])  # 空行
        
        blocks.rows = custom_blocks

    # 生成Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    customer_short = (customer_name or customer_id or "客户").strip()
    filename = f"{timestamp}_{customer_short}_结构化报价.xlsx"
    output_path = os.path.join(output_dir, filename)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # 写表头块（逐行）
        header_df = pd.DataFrame(blocks.rows)
        header_df.to_excel(writer, index=False, header=False, sheet_name="报价单")

        # 空行分隔
        start_row = len(blocks.rows) + 1

        # 写明细标题与数据
        pd.DataFrame([STANDARD_COLUMNS]).to_excel(
            writer, index=False, header=False, startrow=start_row, sheet_name="报价单"
        )
        data_start = start_row + 1
        if not data_df.empty:
            data_df.to_excel(writer, index=False, header=False, startrow=data_start, sheet_name="报价单")
        else:
            # 写一行提示
            pd.DataFrame([["(未匹配到我司产品)"]]).to_excel(
                writer, index=False, header=False, startrow=data_start, sheet_name="报价单"
            )

        # 汇总区
        summary_start = data_start + (len(data_df) if not data_df.empty else 1) + 1
        
        # 根据税率决定汇总行
        if user_tax_rate == 0.0:
            # 不含税
            summary_df = pd.DataFrame([
                ["小计", subtotal],
                ["合计", total],
            ])
        else:
            # 含税
            summary_df = pd.DataFrame([
                ["小计", subtotal],
                ["税额", tax_amount],
                ["合计", total],
            ])
        summary_df.to_excel(writer, index=False, header=False, startrow=summary_start, sheet_name="报价单")

    return output_path 