"""
测试增强价格匹配功能
"""
import pandas as pd
import os
from improved_price_matcher import ImprovedPriceMatcher
from enhanced_quote_processor import process_quote_with_enhanced_matching

def create_test_data():
    """创建测试数据"""
    
    # 创建测试价格表
    price_data = {
        '型号': [
            'Z41X-16Q',
            'Z41X-25Q', 
            'Q41F-16C',
            'Q41F-25C',
            'D71X-16Q',
            'D71X-25Q',
            'H42X-16Q',
            'H42X-25Q'
        ],
        '规格': [
            'DN50',
            'DN50',
            'DN80',
            'DN80', 
            'DN100',
            'DN100',
            'DN150',
            'DN150'
        ],
        '品牌': [
            '上海沪工',
            '上海良工',
            '上海沪工',
            '上海良工',
            '上海沪工',
            '上海良工',
            '上海沪工',
            '上海良工'
        ],
        '价格': [
            120.50,
            115.80,
            280.00,
            275.50,
            450.00,
            440.00,
            680.00,
            670.00
        ]
    }
    
    price_df = pd.DataFrame(price_data)
    price_file = 'test_price_table.csv'
    price_df.to_csv(price_file, index=False, encoding='utf-8-sig')
    print(f"✅ 创建测试价格表: {price_file}")
    
    # 创建测试询价表
    inquiry_data = {
        '品名': [
            '闸阀',
            '球阀',
            '蝶阀',
            '止回阀',
            '合计'
        ],
        '规格型号': [
            'DN50',
            'DN80',
            'DN100',
            'DN150',
            ''
        ],
        '数量': [
            10,
            5,
            8,
            3,
            ''
        ],
        '单位': [
            '个',
            '个',
            '个',
            '个',
            ''
        ]
    }
    
    inquiry_df = pd.DataFrame(inquiry_data)
    inquiry_file = 'test_inquiry_table.csv'
    inquiry_df.to_csv(inquiry_file, index=False, encoding='utf-8-sig')
    print(f"✅ 创建测试询价表: {inquiry_file}")
    
    return price_file, inquiry_file

def test_price_matcher():
    """测试价格匹配器"""
    print("\n🧪 测试价格匹配器...")
    
    price_file, inquiry_file = create_test_data()
    
    # 创建匹配器
    matcher = ImprovedPriceMatcher()
    
    # 加载价格表
    if matcher.load_price_table(price_file):
        print("✅ 价格表加载成功")
    else:
        print("❌ 价格表加载失败")
        return
    
    # 测试单个产品匹配
    test_cases = [
        ("闸阀", "DN50", ""),
        ("球阀", "DN80", "Q41F-16C"),
        ("蝶阀", "DN100", ""),
        ("止回阀", "DN150", "")
    ]
    
    for product_name, specification, model_code in test_cases:
        print(f"\n🔍 测试匹配: {product_name} {specification}")
        result = matcher.match_product(product_name, specification, model_code)
        
        if result['success']:
            best_match = result['best_match']
            print(f"✅ 匹配成功: {best_match['型号']} - ¥{best_match['价格']}")
        else:
            print(f"❌ 匹配失败: {result.get('error', '未知错误')}")
    
    # 清理测试文件
    try:
        os.remove(price_file)
        os.remove(inquiry_file)
        print(f"\n🗑️ 清理测试文件")
    except:
        pass

def test_enhanced_processor():
    """测试增强报价处理器"""
    print("\n🧪 测试增强报价处理器...")
    
    price_file, inquiry_file = create_test_data()
    output_file = 'test_enhanced_quote.xlsx'
    
    # 使用增强处理器
    result = process_quote_with_enhanced_matching(
        inquiry_file=inquiry_file,
        price_file=price_file,
        output_file=output_file
    )
    
    if result:
        print(f"✅ 增强报价处理成功: {result}")
        
        # 检查输出文件
        if os.path.exists(output_file):
            result_df = pd.read_excel(output_file)
            print(f"📊 输出文件包含 {len(result_df)} 行数据")
            print("📋 输出文件列名:", list(result_df.columns))
            
            # 显示部分结果
            print("\n📄 报价结果预览:")
            for idx, row in result_df.head().iterrows():
                if not pd.isna(row.get('品名')):
                    print(f"   {row.get('品名', '')} - {row.get('匹配型号', '')} - ¥{row.get('单价', 0)} - 总价¥{row.get('总价', 0)}")
    else:
        print("❌ 增强报价处理失败")
    
    # 清理测试文件
    try:
        os.remove(price_file)
        os.remove(inquiry_file)
        if os.path.exists(output_file):
            os.remove(output_file)
        print(f"\n🗑️ 清理测试文件")
    except:
        pass

if __name__ == "__main__":
    print("🚀 开始测试增强价格匹配功能")
    
    # 测试价格匹配器
    test_price_matcher()
    
    # 测试增强处理器
    test_enhanced_processor()
    
    print("\n✅ 测试完成！")