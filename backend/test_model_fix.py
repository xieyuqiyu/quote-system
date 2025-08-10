#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试阀门型号生成修复效果
"""

from valve_model_generator import parse_valve_info

# 创建测试用例列表 - 包括之前有问题的阀门
test_cases = [
    # 原始有问题的型号
    {"name": "UPVC球阀DN50", "specs": "", "expected": "U"},
    {"name": "UPVC球阀DN32", "specs": "", "expected": "U"},
    {"name": "手动闸阀DN1000、PN1 法兰", "specs": "", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN800、PN1 法兰", "specs": "", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN300、PN1 法兰", "specs": "", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN400、PN1 法兰", "specs": "", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN65、PN1 法兰", "specs": "Q41W-16Q", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN200、PN1 法兰", "specs": "Q41W-16Q", "expected": "Z45X-1Q"},
    {"name": "手动闸阀DN32、PN1 法兰", "specs": "D371X-16Q", "expected": "Z41X-1Q"},
    {"name": "闸门 铸水铸DN50", "specs": "D371X-16Q", "expected": "Z"},
    {"name": "阀门 铸铁防止器DN200、PN1.6MPa", "specs": "D371X-16Q", "expected": "HS41X-16Q"},
    {"name": "阀门 倒流防止器DN150、PN1.6MPa", "specs": "Z41T-16Q", "expected": "HS41X-16Q"},
    {"name": "阀门 倒流防止器DN100、PN1.6MPa", "specs": "Z41T-16Q", "expected": "HS41X-16Q"},
    {"name": "阀门 电磁流量计DN1000, 0~1.0m3/s, PN1 HS41X-1Q", "specs": "", "expected": "L04X-1P"},
    {"name": "阀门 电磁流量计DN400, 0~0.2m3/s, PN1, HS41X-1Q", "specs": "", "expected": "L04X-1P"},
    {"name": "阀门 电磁流量计DN800, 0~1.0m3/s, PN1, HS41X-1Q", "specs": "", "expected": "L04X-1P"},
    {"name": "阀门 电磁流量计DN300, 0~0.2m3/s, PN1,", "specs": "", "expected": "L04X-1P"},
    {"name": "阀门 电磁流量计DN250, 0~0.1m3/s, PN1, 200X-16Q", "specs": "", "expected": "L04X-1P"}
]

def run_tests():
    print("\n" + "="*80)
    print("阀门型号生成测试")
    print("="*80)
    
    success_count = 0
    failure_count = 0
    
    for i, test in enumerate(test_cases):
        print(f"\n测试 #{i+1}: '{test['name']}' + '{test['specs']}'")
        print("-" * 60)
        
        # 生成型号
        result = parse_valve_info(test['name'], test['specs'], None, True)
        
        # 检查结果
        expected = test['expected']
        if expected in result:
            print(f"✅ 通过: '{result}' 包含预期的 '{expected}'")
            success_count += 1
        else:
            print(f"❌ 失败: '{result}' 不包含预期的 '{expected}'")
            failure_count += 1
        
        print(f"输入: '{test['name']}' + '{test['specs']}'")
        print(f"输出: '{result}'")
    
    # 打印总结
    print("\n" + "="*80)
    print(f"测试完成: 总计 {len(test_cases)} 个测试")
    print(f"通过: {success_count}, 失败: {failure_count}")
    print(f"通过率: {success_count/len(test_cases)*100:.1f}%")
    print("="*80)

if __name__ == "__main__":
    run_tests() 