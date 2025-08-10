import pandas as pd
import re
from default_rules import DefaultRulesManager
from csv_utils import safe_read_csv, safe_to_csv

def analyze_valve_missing_params(name, specs):
    """分析阀门信息，识别缺失的参数，不应用任何默认规则"""
    print(f"\n🔍 [ANALYZE] 分析阀门缺失参数")
    print(f"📋 [ANALYZE] 输入: name='{name}', specs='{specs}'")
    
    # 处理空值或非字符串类型
    if pd.isna(name) or pd.isna(specs):
        print(f"❌ [ANALYZE] 输入参数为空")
        return None
    
    # 确保是字符串类型
    name = str(name)
    specs = str(specs)
    
    # 提取DN口径和PN压力
    dn_match = re.search(r'DN(\d+)', specs)
    # 优先识别MPa/兆帕等小数压力
    mpa_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(Mpa|MPa|兆帕)', name + ' ' + specs)
    pn = None
    if mpa_match:
        pn = int(float(mpa_match.group(1)) * 10)
    else:
        # 支持PN后跟整数或小数
        pn_match = re.search(r'PN\s*([0-9]+(?:\.[0-9]+)?)', name + ' ' + specs, re.IGNORECASE)
        if pn_match:
            if '.' in pn_match.group(1):
                pn = int(float(pn_match.group(1)) * 10)
            else:
                pn = int(pn_match.group(1))
        else:
            # 兼容原有PN(\d+)正则
            pn_match_int = re.search(r'PN(\d+)', specs)
            if not pn_match_int:
                pn_match_int = re.search(r'PN(\d+)', name)
        if pn_match_int:
            pn = int(pn_match_int.group(1))
        else:
            # 尝试标准PN格式
            pn_match_std = re.search(r'PN\s*[=:：]?\s*(\d+)', name + ' ' + specs, re.IGNORECASE)
            if pn_match_std:
                pn = int(pn_match_std.group(1))
            else:
                # 针对PN16格式的特殊处理
                pn_special_match = re.search(r'PN\s*(\d{1,2})[^0-9]', ' ' + name + ' ' + specs + ' ', re.IGNORECASE)
                if pn_special_match and 1 <= int(pn_special_match.group(1)) <= 64:
                    pn = int(pn_special_match.group(1))
                else:
                    # 识别压力数字，如1.6表示PN16
                    mpa_match2 = re.search(r'([0-9]\.[0-9]+)\s*(Mpa|MPa|兆帕)', name + ' ' + specs)
                    if mpa_match2:
                        pn = int(float(mpa_match2.group(1)) * 10)
                    else:
                        pn = 16  # 默认值
    
    # 初始化基础信息
    valve_info = {
        'product_type': '',
        'drive_mode': '',
        'connection': '',
        'structure': '',
        'sealing': '',
        'pressure': str(pn) if pn else '',
        'material': '',
        'dn': dn,
        'name': name,
        'specs': specs
    }
    
    # 材质识别
    full_text = name + ' ' + specs
    if '不锈钢304' in full_text or '304不锈钢' in full_text:
        valve_info['material'] = 'P'
    elif '不锈钢316' in full_text or '316不锈钢' in full_text:
        valve_info['material'] = 'R'
    elif '不锈钢' in full_text:
        valve_info['material'] = 'P'
    elif '黄铜' in full_text or '铜制' in full_text or ('铜' in full_text and '铜芯' not in full_text):
        valve_info['material'] = 'T'
    elif '碳钢' in full_text or '铸钢' in full_text:
        valve_info['material'] = 'C'
    elif '球墨铸铁' in full_text:
        valve_info['material'] = 'Q'
    elif '灰铸铁' in full_text:
        valve_info['material'] = 'Z'
    elif '可锻铸铁' in full_text:
        valve_info['material'] = 'K'
    else:
        # 默认材质为球墨铸铁
        valve_info['material'] = 'Q'
    
    # 产品类型识别
    if '遥控浮球阀' in name:
        valve_info['product_type'] = '100X'
    elif '泄压' in name or '持压' in name:
        valve_info['product_type'] = '500X'
    elif '减压阀' in name:
        if valve_info['material'] == 'T':
            # 铜减压阀使用标准型号，不需要交互
            return None
        else:
            valve_info['product_type'] = '200X'
    elif '缓闭' in name and '止' in name:
        valve_info['product_type'] = '800X'
    elif '闸阀' in name:
        valve_info['product_type'] = 'Z'
    elif '蝶阀' in name:
        valve_info['product_type'] = 'D'
    elif '球阀' in name:
        valve_info['product_type'] = 'Q'
    elif '止回阀' in name or '逆止阀' in name:
        valve_info['product_type'] = 'H'
    elif '截止阀' in name:
        valve_info['product_type'] = 'J'
    elif '节流阀' in name:
        valve_info['product_type'] = 'L'
    elif '柱塞阀' in name:
        valve_info['product_type'] = 'U'
    elif '隔膜阀' in name:
        valve_info['product_type'] = 'G'
    elif '安全阀' in name:
        if '杠杆' in name:
            valve_info['product_type'] = 'GA'
        else:
            valve_info['product_type'] = 'A'
    elif '疏水阀' in name or '蒸汽疏水阀' in name:
        valve_info['product_type'] = 'S'
    elif '排气阀' in name:
        valve_info['product_type'] = 'P'
    elif '旋塞阀' in name:
        valve_info['product_type'] = 'X'
    elif '过滤器' in name or '倒流防止器' in name:
        # 这些产品有特殊处理逻辑，不需要交互
        return None
    
    # 如果没有识别到产品类型，跳过
    if not valve_info['product_type']:
        print(f"⚠️  [ANALYZE] 未识别的产品类型: {name}")
        return None
    
    # 从名称中提取明确的参数
    if '电磁' in name:
        valve_info['drive_mode'] = '0'
    elif '电动' in name:
        valve_info['drive_mode'] = '9'
    elif '气动' in name:
        valve_info['drive_mode'] = '6'
    elif '液动' in name:
        valve_info['drive_mode'] = '7'
    elif '涡轮' in name or '蜗轮' in name:
        valve_info['drive_mode'] = '3'
    elif '锥齿轮' in name:
        valve_info['drive_mode'] = '5'
    
    if '丝扣' in name or '螺纹' in name:
        valve_info['connection'] = '1'
    elif '法兰' in name:
        valve_info['connection'] = '4'
    elif '对夹' in name:
        valve_info['connection'] = '7'
    elif '卡箍' in name or '沟槽' in name:
        valve_info['connection'] = '8'
    elif '焊接' in name:
        valve_info['connection'] = '6'
    
    if '暗杆' in specs or '暗杆' in name:
        valve_info['structure'] = '5'
    elif '明杆' in specs or '明杆' in name:
        valve_info['structure'] = '1'
    elif '橡胶瓣' in name:
        valve_info['structure'] = '4'
    
    if '铜芯' in full_text:
        valve_info['sealing'] = 'T'
    elif valve_info['product_type'] == 'G':
        valve_info['sealing'] = 'J'
    
    # 识别缺失的参数
    missing_params = []
    required_params = ['drive_mode', 'connection', 'structure', 'sealing', 'pressure']
    
    for param in required_params:
        if not valve_info[param]:
            missing_params.append(param)
    
    # 如果没有缺失参数，不需要交互
    if not missing_params:
        print(f"✅ [ANALYZE] 无缺失参数: {name}")
        return None
    
    print(f"🔍 [ANALYZE] 发现缺失参数: {missing_params}")
    return {
        'valve_info': valve_info,
        'missing_params': missing_params
    }

def parse_valve_info_from_combined(combined_info, username=None, use_default_rules=True):
    """从合并的所有单元格信息中解析阀门信息，返回标准型号"""
    print(f"\n{'='*80}")
    print(f"[DEBUG] parse_valve_info_from_combined 开始")
    print(f"[DEBUG] 输入参数:")
    print(f"   combined_info: {combined_info}")
    print(f"   username: {username}")
    print(f"   use_default_rules: {use_default_rules}")
    print(f"{'='*80}")
    
    # 处理空值
    if not combined_info or pd.isna(combined_info):
        print(f"❌ [DEBUG] 输入参数为空，返回空字符串")
        return ''
    
    # 确保是字符串类型
    combined_info = str(combined_info).strip()
    print(f"[DEBUG] 处理后的合并信息: '{combined_info}'")
    
    # 直接使用合并后的完整信息进行解析
    # 作为name参数传入，第二个参数留空
    result = parse_valve_info(combined_info, '', username, use_default_rules)
    
    print(f"[DEBUG] parse_valve_info_from_combined 结束，返回: {result}")
    print(f"{'='*80}\n")
    return result

def parse_valve_info(name, specs, username=None, use_default_rules=True):
    """解析阀门信息，返回型号各部分的代号"""
    import re
    print(f"\n{'='*80}")
    print(f"[DEBUG] parse_valve_info 开始")
    print(f"[DEBUG] 输入参数:")
    print(f"   name: {name}")
    print(f"   specs: {specs}")
    print(f"   username: {username}")
    print(f"   use_default_rules: {use_default_rules}")
    print(f"{'='*80}")
    
    # 处理空值或非字符串类型
    if pd.isna(name) or pd.isna(specs):
        print(f"❌ [DEBUG] 输入参数为空，返回空字符串")
        return ''
    
    # 确保是字符串类型
    name = str(name)
    specs = str(specs)
    print(f"[DEBUG] 转换后的参数: name='{name}', specs='{specs}'")
    
    # 合并名称和规格以便全文搜索
    full_text = name + ' ' + specs
    print(f"[DEBUG] 全文搜索内容: '{full_text}'")
    
    # 提取DN口径
    dn_match = re.search(r'DN(\d+)', specs)
    dn = int(dn_match.group(1)) if dn_match else 50  # 未匹配到DN时默认50
    
    # 优化后的PN提取逻辑
    def extract_pn(text, default_pn=16):
        # 1. 优先识别 MPa/兆帕（如 1.0MPa、1.6兆帕）
        mpa_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(Mpa|MPa|兆帕)', text, re.IGNORECASE)
        if mpa_match:
            return int(float(mpa_match.group(1)) * 10)
        # 2. 识别 PN 后跟数字（如 PN1.0、PN16、PN 1.6）
        pn_match = re.search(r'PN[\s:：=]*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if pn_match:
            value = pn_match.group(1)
            if '.' in value:
                return int(float(value) * 10)
            else:
                return int(value)
        # 3. 兼容“PN16”紧贴写法
        pn_match_int = re.search(r'PN(\d+)', text)
        if pn_match_int:
            return int(pn_match_int.group(1))
        # 4. 没有找到，返回默认值
        return default_pn
    
    pn = extract_pn(full_text, default_pn=16)
    print(f"[DEBUG] 提取到的PN: {pn}")

    # 压力代号（10倍MPa）
    pressure_code = str(pn)
    
    # 初始化基础信息
    valve_type = ''
    drive_mode = ''
    connection = ''
    structure = ''
    sealing = ''
    material = 'Q'  # 默认球墨铸铁
    
    print(f"[DEBUG] 初始化基础信息: valve_type='', drive_mode='', connection='', structure='', sealing='', material='Q'")
    
    # 材质识别（优先级高，先判断）- 同时检查name和specs
    full_text = name + ' ' + specs
    print(f"[DEBUG] 材质识别 - 全文本: '{full_text}'")
    if 'UPVC' in full_text or 'upvc' in full_text.lower() or 'PVC' in full_text:
        material = 'U'  # UPVC塑料
        print(f"[DEBUG] 材质识别: UPVC/PVC -> material='U'")
    elif 'PP' in full_text or 'pp塑料' in full_text.lower():
        material = 'V'  # PP塑料
        print(f"[DEBUG] 材质识别: PP塑料 -> material='V'")
    elif '不锈钢304' in full_text or '304不锈钢' in full_text:
        material = 'P'  # 铬镍系不锈钢
        print(f"[DEBUG] 材质识别: 304不锈钢 -> material='P'")
    elif '不锈钢316' in full_text or '316不锈钢' in full_text:
        material = 'R'  # 铬镍钼系不锈钢  
        print(f"[DEBUG] 材质识别: 316不锈钢 -> material='R'")
    elif '不锈钢' in full_text:
        material = 'P'  # 默认304不锈钢
        print(f"[DEBUG] 材质识别: 不锈钢 -> material='P'")
    elif '黄铜' in full_text or '铜制' in full_text or ('铜' in full_text and '铜芯' not in full_text):
        material = 'T'  # 铜及铜合金
        print(f"[DEBUG] 材质识别: 铜材质 -> material='T'")
    elif '碳钢' in full_text:
        material = 'C'  # 碳钢
        print(f"[DEBUG] 材质识别: 碳钢 -> material='C'")
    elif '铸钢' in full_text:
        material = 'C'  # 碳钢
        print(f"[DEBUG] 材质识别: 铸钢 -> material='C'")
    elif '球墨铸铁' in full_text:
        material = 'Q'  # 球墨铸铁
        print(f"[DEBUG] 材质识别: 球墨铸铁 -> material='Q'")
    elif '灰铸铁' in full_text:
        material = 'Z'  # 灰铸铁
        print(f"[DEBUG] 材质识别: 灰铸铁 -> material='Z'")
    elif '可锻铸铁' in full_text:
        material = 'K'  # 可锻铸铁
        print(f"[DEBUG] 材质识别: 可锻铸铁 -> material='K'")
    else:
        print(f"[DEBUG] 材质识别: 未匹配特殊材质，保持默认 -> material='Q'")

    # 检查是否有铜芯密封面
    has_copper_core = '铜芯' in full_text
    print(f"[DEBUG] 铜芯检查: has_copper_core={has_copper_core}")

    # 产品类型、驱动方式、连接方式、结构、密封等全部用full_text判断
    print(f"\n🏷️  [DEBUG] 第一步：识别产品类型")
    # 先处理特殊产品（新标准）
    if '铸铁镶铜闸阀' in full_text or '给水闸阀' in full_text or ('铸铁' in full_text and '闸阀' in full_text):
        valve_type = 'Z'
        sealing = 'T'  # 铜芯密封
        material = 'Q'  # 球墨铸铁
        structure = '1'  # 明杆
        if not connection:
            connection = '4'  # 默认法兰
        print(f"[DEBUG] 产品类型识别: 铸铁镶铜闸阀/给水闸阀 -> 特殊处理")
    elif '电磁流量计' in full_text:
        valve_type = 'L'  # 流量计作为测量仪表使用L型号
        drive_mode = '0'  # 电磁类型
        connection = '4'  # 默认法兰连接
        structure = '1'   # 默认结构
        sealing = 'X'     # 默认密封
        material = 'P'    # 默认不锈钢
        
        # 返回标准型号
        result = f"L04X-{pressure_code}P"
        print(f"[DEBUG] 产品类型识别: 电磁流量计，直接返回 -> {result}")
        return result
    elif '遥控浮球阀' in full_text:
        valve_type = '100X'
        print(f"[DEBUG] 产品类型识别: 遥控浮球阀 -> valve_type='100X'")
    elif '泄压' in full_text or '持压' in full_text:
        valve_type = '500X'
        print(f"[DEBUG] 产品类型识别: 泄压/持压阀 -> valve_type='500X'")
    elif '减压阀' in full_text:
        if material == 'T':  # 铜减压阀使用标准型号
            result = f"Y11X-{pressure_code}T"
            print(f"[DEBUG] 产品类型识别: 铜减压阀，直接返回 -> {result}")
            return result
        else:
            valve_type = '200X'
            print(f"[DEBUG] 产品类型识别: 减压阀 -> valve_type='200X'")
    elif '缓闭' in full_text and '止' in full_text:
        valve_type = '800X'
        print(f"[DEBUG] 产品类型识别: 缓闭止回阀 -> valve_type='800X'")
    # 常规产品
    elif '闸阀' in full_text:
        valve_type = 'Z'
        print(f"[DEBUG] 产品类型识别: 闸阀 -> valve_type='Z'")
    elif '蝶阀' in full_text:
        valve_type = 'D'
        print(f"[DEBUG] 产品类型识别: 蝶阀 -> valve_type='D'")
    elif '球阀' in full_text:
        valve_type = 'Q'
        print(f"[DEBUG] 产品类型识别: 球阀 -> valve_type='Q'")
    elif '止回阀' in full_text or '逆止阀' in full_text:
        valve_type = 'H'
        print(f"[DEBUG] 产品类型识别: 止回阀 -> valve_type='H'")
    elif '截止阀' in full_text:
        valve_type = 'J'
        print(f"[DEBUG] 产品类型识别: 截止阀 -> valve_type='J'")
    elif '节流阀' in full_text:
        valve_type = 'L'
        print(f"[DEBUG] 产品类型识别: 节流阀 -> valve_type='L'")
    elif '柱塞阀' in full_text:
        valve_type = 'U'
        print(f"[DEBUG] 产品类型识别: 柱塞阀 -> valve_type='U'")
    elif '隔膜阀' in full_text:
        valve_type = 'G'
        print(f"[DEBUG] 产品类型识别: 隔膜阀 -> valve_type='G'")
    elif '安全阀' in full_text:
        if '杠杆' in full_text:
            valve_type = 'GA'
            print(f"[DEBUG] 产品类型识别: 杠杆式安全阀 -> valve_type='GA'")
        else:
            valve_type = 'A'
            print(f"[DEBUG] 产品类型识别: 安全阀 -> valve_type='A'")
    elif '疏水阀' in full_text or '蒸汽疏水阀' in full_text:
        valve_type = 'S'
        print(f"[DEBUG] 产品类型识别: 疏水阀 -> valve_type='S'")
    elif '排气阀' in full_text:
        valve_type = 'P'
        print(f"[DEBUG] 产品类型识别: 排气阀 -> valve_type='P'")
    elif '旋塞阀' in full_text:
        valve_type = 'X'
        print(f"[DEBUG] 产品类型识别: 旋塞阀 -> valve_type='X'")
    # 特殊处理的产品
    elif '过滤器' in full_text:
        # 过滤器特殊处理，直接返回
        if material in ['P', 'R']:
            if dn <= 40:
                result = f"GL11W-{pressure_code}{material}"
            else:
                result = f"GL41W-{pressure_code}{material}"
        elif material == 'U':  # UPVC过滤器
            result = f"GL11U-{pressure_code}U" 
        else:
            result = f"GL41H-{pressure_code}{material}"
        print(f"[DEBUG] 产品类型识别: 过滤器，直接返回 -> {result}")
        return result
    elif '倒流防止器' in full_text or '逆流防止器' in full_text or '防回流' in full_text:
        # 倒流防止器特殊处理，直接返回
        if pn is None:
            pressure_code = '16'
        if '低阻力' in full_text:
            result = f"LHS41X-{pressure_code}{material}"
        else:
            result = f"HS41X-{pressure_code}{material}"
        print(f"[DEBUG] 产品类型识别: 倒流防止器，直接返回 -> {result}")
        return result
    else:
        print(f"❌ [DEBUG] 产品类型识别: 未识别的产品类型")
    
    # 如果没有识别到产品类型，返回空
    if not valve_type:
        print(f"⚠️  [DEBUG] 未识别的产品类型: {name}，返回空字符串")
        return ''
    
    print(f"✅ [DEBUG] 产品类型识别完成: valve_type='{valve_type}'")
    
    # 第二步：从名称中提取明确的驱动方式
    print(f"\n🚗 [DEBUG] 第二步：提取驱动方式")
    if '电磁' in full_text:
        drive_mode = '0'
        print(f"[DEBUG] 驱动方式识别: 电磁 -> drive_mode='0'")
    elif '电动' in full_text:
        drive_mode = '9'
        print(f"[DEBUG] 驱动方式识别: 电动 -> drive_mode='9'")
    elif '气动' in full_text:
        drive_mode = '6'
        print(f"[DEBUG] 驱动方式识别: 气动 -> drive_mode='6'")
    elif '液动' in full_text:
        drive_mode = '7'
        print(f"[DEBUG] 驱动方式识别: 液动 -> drive_mode='7'")
    elif '涡轮' in full_text or '蜗轮' in full_text:
        drive_mode = '3'
        print(f"[DEBUG] 驱动方式识别: 涡轮/蜗轮 -> drive_mode='3'")
    elif '锥齿轮' in full_text:
        drive_mode = '5'
        print(f"[DEBUG] 驱动方式识别: 锥齿轮 -> drive_mode='5'")
    elif '手动' in full_text or '手柄' in full_text or '手轮' in full_text:
        drive_mode = '3'  # 手动为3
        print(f"[DEBUG] 驱动方式识别: 手动/手柄/手轮 -> drive_mode='3'")
    else:
        print(f"[DEBUG] 驱动方式识别: 未匹配，保持空值 -> drive_mode=''")
    
    # 第三步：从名称中提取明确的连接方式
    print(f"\n🔗 [DEBUG] 第三步：提取连接方式")
    if '丝扣' in full_text or '螺纹' in full_text or '内螺纹' in full_text:
        connection = '1'
        print(f"[DEBUG] 连接方式识别: 丝扣/螺纹 -> connection='1'")
    elif '外螺纹' in full_text:
        connection = '2'
        print(f"[DEBUG] 连接方式识别: 外螺纹 -> connection='2'")
    elif '法兰' in full_text:
        connection = '4'
        print(f"[DEBUG] 连接方式识别: 法兰 -> connection='4'")
    elif '对夹' in full_text:
        connection = '7'
        print(f"[DEBUG] 连接方式识别: 对夹 -> connection='7'")
    elif '卡箍' in full_text or '沟槽' in full_text or '快装' in full_text:
        connection = '8'
        print(f"[DEBUG] 连接方式识别: 卡箍/沟槽/快装 -> connection='8'")
    elif '焊接' in full_text or '承插' in full_text:
        connection = '6'
        print(f"[DEBUG] 连接方式识别: 焊接/承插 -> connection='6'")
    else:
        print(f"[DEBUG] 连接方式识别: 未匹配，保持空值 -> connection=''")
    
    # 第四步：从名称中提取明确的结构信息
    print(f"\n🏗️  [DEBUG] 第四步：提取结构信息")
    if '暗杆' in full_text or '暗杆' in name:
        structure = '5'
        print(f"[DEBUG] 结构识别: 暗杆 -> structure='5'")
    elif '明杆' in full_text or '明杆' in name:
        structure = '1'
        print(f"[DEBUG] 结构识别: 明杆 -> structure='1'")
    elif '橡胶瓣' in name:
        structure = '4'
        print(f"[DEBUG] 结构识别: 橡胶瓣 -> structure='4'")
    else:
        print(f"[DEBUG] 结构识别: 未匹配，保持空值 -> structure=''")
    
    # 第五步：从名称中提取明确的密封材料
    print(f"\n🔒 [DEBUG] 第五步：提取密封材料")
    if has_copper_core:
        sealing = 'T'
        print(f"[DEBUG] 密封材料识别: 铜芯 -> sealing='T'")
    elif valve_type == 'G':  # 隔膜阀默认衬胶
        sealing = 'J'
        print(f"[DEBUG] 密封材料识别: 隔膜阀默认衬胶 -> sealing='J'")
    else:
        print(f"[DEBUG] 密封材料识别: 未匹配，保持空值 -> sealing=''")
    
    # 创建阀门信息字典
    valve_info = {
        'product_type': valve_type,
        'drive_mode': drive_mode,
        'connection': connection,
        'structure': structure,
        'sealing': sealing,
        'pressure': pressure_code,
        'material': material,
        'dn': dn,
        'name': name,
        'specs': specs
    }
    
    print(f"\n📋 [DEBUG] 基础解析完成，创建阀门信息字典:")
    for key, value in valve_info.items():
        print(f"   {key}: '{value}'")
    
    # 第六步：应用用户默认规则（从用户的default_rules.json文件中读取）
    print(f"\n🔧 [DEBUG] 第六步：应用用户默认规则")
    print(f"   use_default_rules: {use_default_rules}")
    print(f"   username: {username}")
    print(f"   valve_type: {valve_type}")
    
    if use_default_rules and username and valve_type:
        print(f"🔧 [DEBUG] 开始应用用户默认规则: username={username}, valve_type={valve_type}")
        try:
            # 获取当前脚本所在目录的绝对路径
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_root = os.path.join(current_dir, "merchant_data")
            print(f"[DEBUG] 规则管理器数据根目录: {data_root}")
            
            rules_manager = DefaultRulesManager(data_root)
            # 使用 apply_default_rules 方法，确保所有逻辑统一
            valve_info = rules_manager.apply_default_rules(username, valve_info)
                
        except Exception as e:
            print(f"❌ [DEBUG] 应用用户默认规则时出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚪ [DEBUG] 跳过用户默认规则应用")
        if not use_default_rules:
            print(f"   原因: use_default_rules=False")
        if not username:
            print(f"   原因: username为空")
        if not valve_type:
            print(f"   原因: valve_type为空")
    
    # 第七步：应用代码中的智能推断规则（只填充仍然为空的值）
    print(f"\n🧠 [DEBUG] 第七步：应用智能推断规则")
    
    # 连接方式智能推断
    print(f"🔗 [DEBUG] 连接方式智能推断:")
    print(f"   当前connection: '{valve_info.get('connection')}'")
    if not valve_info.get('connection'):
        if valve_type == 'D':  # 蝶阀默认对夹
            valve_info['connection'] = '7'
            print(f"[DEBUG] 蝶阀默认对夹 -> connection='7'")
        elif dn <= 40:  # 小口径默认丝口
            valve_info['connection'] = '1'
            print(f"[DEBUG] 小口径默认丝口 (DN={dn}) -> connection='1'")
        else:  # 大口径默认法兰
            valve_info['connection'] = '4'
            print(f"[DEBUG] 大口径默认法兰 (DN={dn}) -> connection='4'")
        
        # 材质特殊规则
        if material == 'T' and dn < 100:  # 铜阀门小于DN100全部丝口
            valve_info['connection'] = '1'
            print(f"[DEBUG] 铜阀门小于DN100全部丝口 -> connection='1'")
        elif material in ['P', 'R'] and dn <= 40:  # 不锈钢小于等于DN40全部丝口
            valve_info['connection'] = '1'
            print(f"[DEBUG] 不锈钢小于等于DN40全部丝口 -> connection='1'")
        
        print(f"[DEBUG] 最终推断连接方式: connection='{valve_info['connection']}'")
    else:
        print(f"✅ [DEBUG] 连接方式已设置，跳过推断")
    
    # 结构形式智能推断
    print(f"🏗️  [DEBUG] 结构形式智能推断:")
    print(f"   当前structure: '{valve_info.get('structure')}'")
    if not valve_info.get('structure'):
        if valve_type == 'Z':  # 闸阀
            if material == 'T':  # 铜闸阀默认暗杆
                valve_info['structure'] = '5'
                print(f"[DEBUG] 铜闸阀默认暗杆 -> structure='5'")
            else:
                # 修正闸阀结构形式判断：DN≤50为明杆(1)，DN>50为暗杆(5)
                valve_info['structure'] = '1' if dn <= 50 else '5'
                print(f"[DEBUG] 闸阀结构推断 (DN={dn}) -> structure='{valve_info['structure']}'")
        else:
            valve_info['structure'] = '1'  # 其他阀门默认结构1
            print(f"[DEBUG] 其他阀门默认结构1 -> structure='1'")
        print(f"[DEBUG] 最终推断结构形式: structure='{valve_info['structure']}'")
    else:
        print(f"✅ [DEBUG] 结构形式已设置，跳过推断")
    
    # 密封材料智能推断
    print(f"🔒 [DEBUG] 密封材料智能推断:")
    print(f"   当前sealing: '{valve_info.get('sealing')}'")
    if not valve_info.get('sealing'):
        if material == 'T':  # 铜阀门
            if valve_type == 'Q':  # 铜球阀用四氟
                valve_info['sealing'] = 'F'
                print(f"[DEBUG] 铜球阀用四氟 -> sealing='F'")
            else:  # 其他铜阀门用本体密封
                valve_info['sealing'] = 'W'
                print(f"[DEBUG] 其他铜阀门用本体密封 -> sealing='W'")
        elif material in ['P', 'R']:  # 不锈钢阀门
            if valve_type == 'Q':  # 不锈钢球阀用四氟
                valve_info['sealing'] = 'F'
                print(f"[DEBUG] 不锈钢球阀用四氟 -> sealing='F'")
            else:  # 其他不锈钢阀门用本体密封
                valve_info['sealing'] = 'W'
                print(f"[DEBUG] 其他不锈钢阀门用本体密封 -> sealing='W'")
        else:  # 其他材质默认橡胶密封
            valve_info['sealing'] = 'X'
            print(f"[DEBUG] 其他材质默认橡胶密封 -> sealing='X'")
        print(f"[DEBUG] 最终推断密封材料: sealing='{valve_info['sealing']}'")
    else:
        print(f"✅ [DEBUG] 密封材料已设置，跳过推断")
    
    # 驱动方式智能推断
    print(f"🚗 [DEBUG] 驱动方式智能推断:")
    print(f"   当前drive_mode: '{valve_info.get('drive_mode')}'")
    if not valve_info.get('drive_mode'):
        if valve_type == 'D' and dn >= 125:  # 大口径蝶阀默认蜗轮
            valve_info['drive_mode'] = '3'
            print(f"[DEBUG] 大口径蝶阀默认蜗轮 (DN={dn}) -> drive_mode='3'")
        # 其他情况保持空（手动）
        if valve_info.get('drive_mode'):
            print(f"[DEBUG] 最终推断驱动方式: drive_mode='{valve_info['drive_mode']}'")
        else:
            print(f"[DEBUG] 保持手动驱动: drive_mode=''")
    else:
        print(f"✅ [DEBUG] 驱动方式已设置，跳过推断")
    
    print(f"\n📋 [DEBUG] 智能推断完成，最终参数:")
    for key, value in valve_info.items():
        print(f"   {key}: '{value}'")
    
    # 第八步：组合型号
    print(f"\n🏷️  [DEBUG] 第八步：组合型号")
    drive_mode = valve_info.get('drive_mode', '')
    connection = valve_info.get('connection', '')
    structure = valve_info.get('structure', '')
    sealing = valve_info.get('sealing', '')
    pressure_code = valve_info.get('pressure', pressure_code)
    material = valve_info.get('material', material)
    
    print(f"[DEBUG] 型号组合参数:")
    print(f"   valve_type: '{valve_type}'")
    print(f"   drive_mode: '{drive_mode}'")
    print(f"   connection: '{connection}'")
    print(f"   structure: '{structure}'")
    print(f"   sealing: '{sealing}'")
    print(f"   pressure_code: '{pressure_code}'")
    print(f"   material: '{material}'")
    
    # 对于特殊产品，直接返回完整型号
    if valve_type in ['100X', '200X', '500X', '800X']:
        model = ""
        if connection == '8':
            model = "8"
        model += valve_type + f"-{pressure_code}{material}"
        print(f"[DEBUG] 生成特殊产品型号: {model}")
        print(f"{'='*80}")
        return model

    # 组合标准型号
    model = valve_type
    print(f"[DEBUG] 开始组合标准型号: '{model}'")
    
    # 驱动方式（手动默认不标）
    if drive_mode:
        model += drive_mode
        print(f"[DEBUG] 添加驱动方式: '{model}'")
    
    # 连接方式
    model += connection
    print(f"[DEBUG] 添加连接方式: '{model}'")
    
    # 结构形式
    model += structure
    print(f"[DEBUG] 添加结构形式: '{model}'")
    
    # 密封材料
    model += sealing
    print(f"[DEBUG] 添加密封材料: '{model}'")
    
    # 压力-材料
    model += f"-{pressure_code}{material}"
    print(f"[DEBUG] 添加压力-材料: '{model}'")
    
    print(f"[DEBUG] 生成标准型号: {model}")
    print(f"{'='*80}")
    print(f"🎯 [DEBUG] parse_valve_info 结束，返回: {model}")
    print(f"{'='*80}\n")
    return model

def generate_valve_models(input_dir='./规范后客户询价表数据', output_dir='./型号编码后的询价表数据', username=None, use_default_rules=True):
   """读取询价表目录下的所有CSV文件，生成型号，并保存到输出目录"""
   import os
   
   # 确保输出目录存在
   os.makedirs(output_dir, exist_ok=True)
   
   # 遍历输入目录下的所有CSV文件
   for filename in os.listdir(input_dir):
       if filename.endswith('.csv'):
           input_file = os.path.join(input_dir, filename)
           output_file = os.path.join(output_dir, filename)
           
           try:
               # 使用安全的CSV读取函数
               df = safe_read_csv(input_file)
               
               # 生成型号列（只用品名字段，不用规格型号字段）
               models = []
               for _, row in df.iterrows():
                   if pd.isna(row['品名']) or row['品名'] == '合计':
                       models.append('')
                   else:
                       model = parse_valve_info(row['品名'], '', username, use_default_rules)
                       models.append(model)
               
               # 添加型号列
               df['标准型号'] = models
               
               # 使用安全的CSV保存函数
               safe_to_csv(df, output_file)
               print(f"型号匹配完成！{filename} 已保存到 {output_file}")
               
               # 打印前几个结果预览
               print(f"\n{filename} 型号匹配预览：")
               for i in range(min(10, len(df))):
                   if df.iloc[i]['品名'] and df.iloc[i]['品名'] != '合计':
                       print(f"{df.iloc[i]['品名']} | -> {df.iloc[i]['标准型号']}")
               print("-" * 50)
               
           except Exception as e:
               print(f"❌ 处理文件 {filename} 时出错: {e}")
               import traceback
               traceback.print_exc()
               continue

if __name__ == "__main__":
    generate_valve_models()