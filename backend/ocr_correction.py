import re
from typing import List, Dict, Tuple, Any

class OCRCorrector:
    """OCR文本修正器，专门用于处理阀门规格文本"""
    
    def __init__(self):
        # 常见的OCR错误映射
        self.ocr_fixes = {
            # 数字识别错误
            'I': '1',  # 大写I经常被识别为数字1
            'l': '1',  # 小写l经常被识别为数字1
            'O': '0',  # 大写O经常被识别为数字0
            'o': '0',  # 小写o经常被识别为数字0
            'S': '5',  # 大写S经常被识别为数字5
            's': '5',  # 小写s经常被识别为数字5
            'Z': '2',  # 大写Z经常被识别为数字2
            'z': '2',  # 小写z经常被识别为数字2
            'G': '6',  # 大写G经常被识别为数字6
            'g': '6',  # 小写g经常被识别为数字6
            'B': '8',  # 大写B经常被识别为数字8
            'b': '8',  # 小写b经常被识别为数字8
            
            # 特殊字符修正
            '．': '.',  # 全角句号
            '，': ',',  # 全角逗号
            '：': ':',  # 全角冒号
            '；': ';',  # 全角分号
        }
        
        # 常见的阀门规格模式
        self.dn_patterns = [
            r'DN\s*(\d+)',  # DN100, DN 100
            r'D\s*(\d+)',   # D100, D 100
            r'(\d+)\s*DN',  # 100 DN
            r'(\d+)\s*D',   # 100 D
        ]
        
        # 数量模式
        self.quantity_patterns = [
            r'(\d+)\s*个',
            r'(\d+)\s*件',
            r'(\d+)\s*台',
            r'(\d+)\s*套',
            r'(\d+)\s*只',
            r'(\d+)\s*支',
            r'(\d+)\s*根',
            r'(\d+)\s*条',
            r'(\d+)\s*米',
            r'(\d+)\s*米',
            r'(\d+)\s*mm',
            r'(\d+)\s*MM',
        ]

    def fix_ocr_errors(self, text: str) -> str:
        """修正OCR识别错误"""
        corrected_text = text
        
        # 应用字符替换
        for wrong_char, correct_char in self.ocr_fixes.items():
            corrected_text = corrected_text.replace(wrong_char, correct_char)
        
        # 修正常见的OCR错误组合
        corrections = [
            ('DNI', 'DN1'),  # DNI -> DN1
            ('DNI0', 'DN10'),  # DNI0 -> DN10
            ('DNI00', 'DN100'),  # DNI00 -> DN100
            ('DNI50', 'DN150'),  # DNI50 -> DN150
            ('DNSO', 'DN50'),  # DNSO -> DN50
            ('DNS', 'DN5'),  # DNS -> DN5
            ('D L', 'DN'),  # D L -> DN
            ('D 25', 'DN25'),  # D 25 -> DN25
            ('D 50', 'DN50'),  # D 50 -> DN50
            ('D 100', 'DN100'),  # D 100 -> DN100
            ('D 150', 'DN150'),  # D 150 -> DN150
        ]
        
        for wrong, correct in corrections:
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text

    def extract_dn_and_quantity(self, text: str) -> List[Dict[str, str]]:
        """从文本中提取DN规格和数量"""
        results = []
        
        # 修正OCR错误
        corrected_text = self.fix_ocr_errors(text)
        
        # 按行分割
        lines = corrected_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 查找DN规格
            dn_value = None
            for pattern in self.dn_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    dn_value = match.group(1)
                    break
            
            # 查找数量
            quantity = None
            for pattern in self.quantity_patterns:
                match = re.search(pattern, line)
                if match:
                    quantity = match.group(1)
                    break
            
            # 如果没有找到明确的数量，尝试从行尾的数字提取
            if not quantity:
                # 查找行尾的数字
                end_numbers = re.findall(r'(\d+)\s*$', line)
                if end_numbers:
                    quantity = end_numbers[-1]
            
            # 如果找到了DN值，添加到结果中
            if dn_value:
                result = {
                    'original_text': line,
                    'corrected_text': line,
                    'dn_value': dn_value,
                    'quantity': quantity or '1',
                    'confidence': 'high' if quantity else 'medium'
                }
                results.append(result)
        
        return results

    def process_ocr_text(self, text: str) -> Dict[str, Any]:
        """处理OCR文本，返回修正后的结果"""
        # 修正OCR错误
        corrected_text = self.fix_ocr_errors(text)
        
        # 提取规格和数量
        extracted_data = self.extract_dn_and_quantity(corrected_text)
        
        # 统计信息
        stats = {
            'original_lines': len([line for line in text.split('\n') if line.strip()]),
            'corrected_lines': len([line for line in corrected_text.split('\n') if line.strip()]),
            'extracted_items': len(extracted_data),
            'corrections_made': self.count_corrections(text, corrected_text)
        }
        
        return {
            'original_text': text,
            'corrected_text': corrected_text,
            'extracted_data': extracted_data,
            'statistics': stats
        }

    def count_corrections(self, original: str, corrected: str) -> int:
        """统计修正的数量"""
        corrections = 0
        for wrong_char, correct_char in self.ocr_fixes.items():
            corrections += original.count(wrong_char)
        return corrections

    def format_results(self, results: Dict[str, Any]) -> str:
        """格式化结果为可读的字符串"""
        output = []
        output.append("=== OCR修正结果 ===")
        output.append(f"原始文本行数: {results['statistics']['original_lines']}")
        output.append(f"修正后行数: {results['statistics']['corrected_lines']}")
        output.append(f"提取项目数: {results['statistics']['extracted_items']}")
        output.append(f"修正字符数: {results['statistics']['corrections_made']}")
        output.append("")
        
        output.append("=== 修正对比 ===")
        original_lines = results['original_text'].split('\n')
        corrected_lines = results['corrected_text'].split('\n')
        
        for i, (orig, corr) in enumerate(zip(original_lines, corrected_lines)):
            if orig.strip() != corr.strip():
                output.append(f"行 {i+1}:")
                output.append(f"  原始: {orig}")
                output.append(f"  修正: {corr}")
                output.append("")
        
        output.append("=== 提取的规格信息 ===")
        for item in results['extracted_data']:
            output.append(f"DN{item['dn_value']} - 数量: {item['quantity']} (置信度: {item['confidence']})")
            output.append(f"  原始文本: {item['original_text']}")
            output.append("")
        
        return '\n'.join(output)


# 使用示例
if __name__ == "__main__":
    # 测试数据
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
    
    corrector = OCRCorrector()
    results = corrector.process_ocr_text(test_text)
    
    print(corrector.format_results(results)) 