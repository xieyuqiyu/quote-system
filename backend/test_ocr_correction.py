#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ocr_correction import OCRCorrector

def test_ocr_correction():
    """测试OCR修正功能"""
    
    # 你提供的测试数据
    test_text = """ae ETE Gh BoP
DN100. 5     
13
8
DNI50 ni     
DNI00. 2     
DNSO. L      
DN L
D 25
DN"""
    
    print("原始OCR文本:")
    print(test_text)
    print("\n" + "="*50)
    
    # 创建OCR修正器
    corrector = OCRCorrector()
    
    # 处理文本
    results = corrector.process_ocr_text(test_text)
    
    # 显示结果
    print(corrector.format_results(results))
    
    # 显示修正后的完整文本
    print("\n" + "="*50)
    print("修正后的完整文本:")
    print(results['corrected_text'])
    
    # 显示提取的规格信息
    print("\n" + "="*50)
    print("提取的规格信息:")
    for item in results['extracted_data']:
        print(f"DN{item['dn_value']} - 数量: {item['quantity']}")

if __name__ == "__main__":
    test_ocr_correction() 