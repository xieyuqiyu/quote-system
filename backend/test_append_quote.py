from main import append_quote_to_original

append_quote_to_original(
    price_file="merchant_data/admin/价格表/价格 (2).xlsx",
    inquiry_file="merchant_data/admin/询价表/工作簿1.xlsx",
    output_file="merchant_data/admin/报价单/测试输出.csv"
)
print("处理完成，已生成报价单：merchant_data/admin/报价单/测试输出.csv") 