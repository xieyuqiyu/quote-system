#!/usr/bin/env python3
"""
CSV工具模块 - 处理CSV文件编码问题
"""

import pandas as pd
import chardet
import os

def detect_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB来检测编码
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            print(f"🔍 文件编码检测: {file_path}")
            print(f"   检测到编码: {encoding} (置信度: {confidence:.2f})")
            
            # 如果置信度太低，使用常见编码
            if confidence < 0.7:
                print(f"   置信度较低，尝试常见编码")
                return None
            
            return encoding
    except Exception as e:
        print(f"❌ 编码检测失败: {e}")
        return None

def safe_read_csv(file_path, **kwargs):
    """安全读取CSV文件，自动处理编码问题"""
    print(f"📖 安全读取CSV: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 常见的编码列表
    encodings_to_try = [
        'utf-8-sig',  # UTF-8 with BOM
        'utf-8',      # UTF-8
        'gbk',        # 中文GBK
        'gb2312',     # 中文GB2312
        'gb18030',    # 中文GB18030
        'big5',       # 繁体中文
        'latin1',     # ISO-8859-1
        'cp1252',     # Windows-1252
        'ascii'       # ASCII
    ]
    
    # 首先尝试检测编码
    detected_encoding = detect_encoding(file_path)
    if detected_encoding:
        encodings_to_try.insert(0, detected_encoding)
    
    # 尝试不同的编码
    for encoding in encodings_to_try:
        try:
            print(f"🔄 尝试编码: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding, **kwargs)
            print(f"✅ 成功使用编码: {encoding}")
            print(f"📊 读取数据: {len(df)} 行 x {len(df.columns)} 列")
            return df
        except UnicodeDecodeError as e:
            print(f"❌ 编码 {encoding} 失败: {e}")
            continue
        except Exception as e:
            print(f"❌ 读取失败 ({encoding}): {e}")
            continue
    
    # 如果所有编码都失败，尝试忽略错误
    try:
        print("🔄 尝试忽略编码错误...")
        df = pd.read_csv(file_path, encoding='utf-8', errors='ignore', **kwargs)
        print("✅ 使用忽略错误模式成功读取")
        return df
    except Exception as e:
        print(f"❌ 忽略错误模式也失败: {e}")
    
    # 最后尝试二进制模式读取并转换
    try:
        print("🔄 尝试二进制模式读取...")
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 尝试解码为字符串
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                text_content = content.decode(encoding, errors='replace')
                # 写入临时文件
                temp_file = file_path + '.temp.csv'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                df = pd.read_csv(temp_file, **kwargs)
                os.remove(temp_file)  # 删除临时文件
                print(f"✅ 二进制模式成功 (使用 {encoding})")
                return df
            except Exception:
                continue
    except Exception as e:
        print(f"❌ 二进制模式失败: {e}")
    
    raise ValueError(f"无法读取CSV文件 {file_path}，尝试了所有可能的编码方式")

def safe_to_csv(df, file_path, **kwargs):
    """安全保存CSV文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 默认使用UTF-8 with BOM编码
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'utf-8-sig'
        
        if 'index' not in kwargs:
            kwargs['index'] = False
        
        df.to_csv(file_path, **kwargs)
        print(f"✅ CSV保存成功: {file_path}")
        return True
    except Exception as e:
        print(f"❌ CSV保存失败: {e}")
        return False

def convert_csv_encoding(input_file, output_file, target_encoding='utf-8-sig'):
    """转换CSV文件编码"""
    try:
        print(f"🔄 转换CSV编码: {input_file} -> {output_file}")
        
        # 读取原文件
        df = safe_read_csv(input_file)
        
        # 保存为目标编码
        safe_to_csv(df, output_file, encoding=target_encoding)
        
        print(f"✅ 编码转换完成")
        return True
    except Exception as e:
        print(f"❌ 编码转换失败: {e}")
        return False

if __name__ == "__main__":
    # 测试函数
    test_file = "test.csv"
    if os.path.exists(test_file):
        try:
            df = safe_read_csv(test_file)
            print("测试成功!")
            print(df.head())
        except Exception as e:
            print(f"测试失败: {e}")
    else:
        print("测试文件不存在") 