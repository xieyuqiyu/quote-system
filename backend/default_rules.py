import json
import os
from typing import Dict, List, Any, Optional

class DefaultRulesManager:
    """默认规则管理器"""
    
    def __init__(self, data_root: str = None):
        # 修复路径问题 - 使用绝对路径
        if data_root is None:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_root = os.path.join(current_dir, "merchant_data")
        else:
            self.data_root = data_root
        
        print(f"🔍 DefaultRulesManager 初始化，数据根目录: {self.data_root}")
        
        # 默认驱动方式选项
        self.drive_modes = {
            "": "手动（默认）",
            "0": "电磁动",
            "1": "电磁-液动", 
            "2": "电-液动",
            "3": "蜗轮",
            "4": "正齿轮",
            "5": "锥齿轮",
            "6": "气动",
            "6K": "常开式气动",
            "6B": "常闭式气动",
            "7": "液动",
            "7K": "常开式液动",
            "7B": "常闭式液动",
            "8": "气-液动",
            "9": "电动",
            "9B": "防爆电动"
        }
        
        # 默认连接方式选项
        self.connection_types = {
            "1": "内螺纹",
            "2": "外螺纹",
            "4": "法兰式",
            "6": "焊接式",
            "7": "对夹",
            "8": "卡箍/沟槽",
            "9": "卡套"
        }
        
        # 默认结构形式选项（按产品类型分类）
        self.structure_forms = {
            "Z": {  # 闸阀
                "0": "阀杆升降式(明杆) - 楔式闸板 - 弹性闸板",
                "1": "阀杆升降式(明杆) - 楔式闸板 - 刚性单闸板",
                "2": "阀杆升降式(明杆) - 楔式闸板 - 刚性双闸板",
                "3": "阀杆升降式(明杆) - 平行式闸板 - 单闸板",
                "4": "阀杆升降式(明杆) - 平行式闸板 - 双闸板",
                "5": "阀杆非升降式(暗杆) - 单闸板",
                "6": "阀杆非升降式(暗杆) - 双闸板",
                "7": "阀杆非升降式(暗杆) - 平行式闸板 - 单闸板",
                "8": "阀杆非升降式(暗杆) - 平行式闸板 - 双闸板"
            },
            "D": {  # 蝶阀
                "0": "密封型 - 单偏心",
                "1": "密封型 - 中心垂直板（默认）",
                "2": "密封型 - 双偏心",
                "3": "密封型 - 三偏心",
                "4": "密封型 - 连杆机构",
                "5": "非密封型 - 单偏心",
                "6": "非密封型 - 中心垂直板",
                "7": "非密封型 - 双偏心",
                "8": "非密封型 - 三偏心",
                "9": "非密封型 - 连杆机构"
            },
            "Q": {  # 球阀
                "1": "浮动球 - 直通流道",
                "2": "浮动球 - Y形三通流道",
                "4": "浮动球 - L形三通流道",
                "5": "浮动球 - T形三通流道",
                "6": "固定球 - 四通流道",
                "7": "固定球 - 直通流道",
                "8": "固定球 - T形三通流道",
                "9": "固定球 - L形三通流道",
                "0": "固定球 - 半球直通"
            },
            "H": {  # 止回阀和底阀
                "1": "升降式阀瓣 - 直通流道（默认）",
                "2": "升降式阀瓣 - 立式结构",
                "3": "升降式阀瓣 - 角式流道",
                "4": "旋启式阀瓣 - 单瓣结构（默认）",
                "5": "旋启式阀瓣 - 多瓣结构",
                "6": "旋启式阀瓣 - 双瓣结构",
                "7": "蝶形止回式"
            },
            "J": {  # 截止阀
                "1": "阀瓣非平衡式 - 直通流道",
                "2": "阀瓣非平衡式 - Z形流道",
                "3": "阀瓣非平衡式 - 三通流道",
                "4": "阀瓣非平衡式 - 角式流道",
                "5": "阀瓣非平衡式 - 直流流道",
                "6": "阀瓣平衡式 - 直通流道",
                "7": "阀瓣平衡式 - 角式流道"
            },
            "L": {  # 节流阀
                "1": "阀瓣非平衡式 - 直通流道",
                "2": "阀瓣非平衡式 - Z形流道",
                "3": "阀瓣非平衡式 - 三通流道",
                "4": "阀瓣非平衡式 - 角式流道",
                "5": "阀瓣非平衡式 - 直流流道",
                "6": "阀瓣平衡式 - 直通流道",
                "7": "阀瓣平衡式 - 角式流道"
            },
            "U": {  # 柱塞阀
                "1": "阀瓣非平衡式 - 直通流道",
                "2": "阀瓣非平衡式 - Z形流道",
                "3": "阀瓣非平衡式 - 三通流道",
                "4": "阀瓣非平衡式 - 角式流道",
                "5": "阀瓣非平衡式 - 直流流道",
                "6": "阀瓣平衡式 - 直通流道",
                "7": "阀瓣平衡式 - 角式流道"
            },
            "G": {  # 隔膜阀
                "1": "屋脊流道",
                "5": "直流流道",
                "6": "直通流道",
                "8": "Y形角式流道"
            },
            "A": {  # 安全阀
                "0": "带散热片全启式",
                "1": "弹簧载荷弹簧密封结构 - 微启式",
                "2": "弹簧载荷弹簧密封结构 - 全启式",
                "3": "弹簧载荷弹簧不封闭且带扳手结构 - 微启式、双联阀",
                "4": "弹簧载荷弹簧密封结构 - 带扳手全启式",
                "6": "带控制机构全启式",
                "7": "弹簧载荷弹簧不封闭且带扳手结构 - 微启式",
                "8": "弹簧载荷弹簧不封闭且带扳手结构 - 全启式",
                "9": "脉冲式"
            },
            "GA": {  # 杠杆式安全阀
                "2": "单杠杆",
                "4": "双杠杆"
            },
            "Y": {  # 减压阀
                "1": "薄膜式",
                "2": "弹簧薄膜式",
                "3": "活塞式",
                "4": "波纹管式",
                "5": "杠杆式"
            },
            "S": {  # 蒸汽疏水阀
                "1": "浮球式",
                "3": "浮桶式",
                "4": "液体或固体膨胀式",
                "5": "钟形浮子式",
                "6": "蒸汽压力式或膜盒式",
                "7": "双金属片式",
                "8": "脉冲式",
                "9": "圆盘热动力式"
            },
            "P": {  # 排污阀
                "1": "液面连接排放 - 截止型直通式",
                "2": "液面连接排放 - 截止型角式",
                "5": "液底间断排放 - 截止型直流式",
                "6": "液底间断排放 - 截止型直通式",
                "7": "液底间断排放 - 截止型角式",
                "8": "液底间断排放 - 浮动闸板型直通式"
            },
            "X": {  # 旋塞阀
                "3": "填料密封 - 直通流道",
                "4": "填料密封 - T形三通流道",
                "5": "填料密封 - 四通流道",
                "7": "油密封 - 直通流道",
                "8": "油密封 - T形三通流道"
            }
        }
        
        # 默认密封面材料选项
        self.sealing_materials = {
            "B": "锡基轴承合金(巴氏合金)",
            "C": "搪瓷",
            "D": "渗氮钢",
            "F": "氟塑料",
            "G": "陶瓷",
            "H": "Cr13系不锈钢",
            "J": "衬胶",
            "M": "蒙乃尔合金",
            "N": "尼龙塑料",
            "P": "渗硼钢",
            "Q": "衬铅",
            "R": "奥氏体不锈钢",
            "S": "塑料",
            "T": "铜合金",
            "X": "橡胶",
            "Y": "硬质合金",
            "W": "阀体直接加工"
        }
        
        # 默认压力数值选项
        self.pressure_values = ["6", "10", "16", "25", "40"]
        
        # 默认阀体材质选项
        self.body_materials = {
            "C": "碳钢",
            "H": "Cr13系不锈钢",
            "I": "铬钼系钢",
            "K": "可锻铸铁",
            "L": "铝合金",
            "P": "铬镍系不锈钢",
            "Q": "球墨铸铁",
            "R": "铬镍钼系不锈钢",
            "S": "塑料",
            "T": "铜及铜合金",
            "Ti": "钛及钛合金",
            "V": "铬钼钒钢",
            "Z": "灰铸铁"
        }
        
        # 基础产品类型
        self.basic_product_types = {
            "Z": "闸阀",
            "D": "蝶阀", 
            "Q": "球阀",
            "H": "止回阀",
            "J": "截止阀",
            "L": "节流阀",
            "U": "柱塞阀",
            "G": "隔膜阀",
            "A": "安全阀",
            "GA": "杠杆式安全阀",
            "Y": "减压阀",
            "S": "蒸汽疏水阀",
            "P": "排污阀",
            "X": "旋塞阀"
        }
    
    def get_user_rules_file(self, username: str) -> str:
        """获取用户规则文件路径"""
        user_dir = os.path.join(self.data_root, username)
        rules_file = os.path.join(user_dir, "default_rules.json")
        print(f"🔍 获取用户规则文件路径: {rules_file}")
        print(f"📁 用户目录是否存在: {os.path.exists(user_dir)}")
        print(f"📄 规则文件是否存在: {os.path.exists(rules_file)}")
        
        # 确保用户目录存在
        os.makedirs(user_dir, exist_ok=True)
        return rules_file
    
    def load_user_rules(self, username: str) -> Dict[str, Any]:
        """加载用户的默认规则"""
        rules_file = self.get_user_rules_file(username)
        
        if os.path.exists(rules_file):
            try:
                print(f"📖 正在读取用户规则文件: {rules_file}")
                with open(rules_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📄 文件内容长度: {len(content)} 字符")
                    if content.strip():
                        rules = json.loads(content)
                        print(f"✅ 成功加载用户规则，包含 {len(rules)} 个主要配置项")
                        return rules
                    else:
                        print(f"⚠️  规则文件为空")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
            except Exception as e:
                print(f"❌ 加载用户规则失败: {e}")
        else:
            print(f"⚠️  用户 {username} 的规则文件不存在: {rules_file}")
        
        # 如果用户规则文件不存在或损坏，创建一个默认的
        print(f"🔧 为用户 {username} 创建默认规则文件")
        self.create_default_rules_for_new_user(username)
        
        # 重新尝试加载
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 重新加载用户规则失败: {e}")
        
        # 如果还是失败，返回系统默认规则
        print(f"🔄 返回系统默认规则")
        return self.get_default_rules()
    
    def save_user_rules(self, username: str, rules: Dict[str, Any]) -> bool:
        """保存用户的默认规则"""
        try:
            rules_file = self.get_user_rules_file(username)
            print(f"💾 正在保存用户规则到: {rules_file}")
            
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 用户规则保存成功")
            return True
        except Exception as e:
            print(f"❌ 保存用户规则失败: {e}")
            return False
    
    def create_default_rules_for_new_user(self, username: str) -> bool:
        """为新用户创建默认规则文件"""
        try:
            print(f"🔧 为新用户 {username} 创建默认规则文件")
            
            # 获取模板规则 - 优先使用 dage 用户的规则，否则使用系统默认规则
            template_rules = None
            dage_rules_file = self.get_user_rules_file('dage')
            
            if os.path.exists(dage_rules_file):
                try:
                    with open(dage_rules_file, 'r', encoding='utf-8') as f:
                        template_rules = json.load(f)
                    print(f"✅ 使用 dage 用户的规则作为模板")
                except Exception as e:
                    print(f"⚠️  读取 dage 用户规则失败: {e}")
            
            # 如果没有 dage 用户规则，使用系统默认规则
            if not template_rules:
                template_rules = self.get_default_rules()
                print(f"✅ 使用系统默认规则作为模板")
            
            # 保存为新用户的规则文件
            success = self.save_user_rules(username, template_rules)
            if success:
                print(f"✅ 新用户 {username} 的默认规则文件创建成功")
            else:
                print(f"❌ 新用户 {username} 的默认规则文件创建失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 为用户 {username} 创建默认规则文件时出错: {e}")
            return False
    
    def get_default_rules(self) -> Dict[str, Any]:
        """获取系统默认规则"""
        return {
            "pricing": {
                "discount": 1.0  # 折扣（0-1），1.0 表示不打折
            },
            "product_defaults": {
                "Z": {  # 闸阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接（DN50以上常用）
                    "structure": "1",   # 明杆
                    "sealing": "T",     # 铜芯密封
                    "pressure": "16",
                    "material": "Q"
                },
                "D": {  # 蝶阀默认值
                    "drive_mode": "",
                    "connection": "7",  # 对夹连接（蝶阀常用）
                    "structure": "1",   # 中心垂直板
                    "sealing": "X",     # 橡胶密封
                    "pressure": "16",
                    "material": "Q"
                },
                "Q": {  # 球阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",   # 直通流道
                    "sealing": "W",     # 本体密封
                    "pressure": "16", 
                    "material": "Q"
                },
                "H": {  # 止回阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",   # 升降式
                    "sealing": "T",     # 铜芯密封
                    "pressure": "16",
                    "material": "Q"
                },
                "J": {  # 截止阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",   # 直通流道
                    "sealing": "T",     # 铜芯密封
                    "pressure": "16",
                    "material": "Q"
                },
                "L": {  # 节流阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接（小口径常用）
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "U": {  # 柱塞阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "G": {  # 隔膜阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",
                    "sealing": "J",     # 衬胶
                    "pressure": "16",
                    "material": "Q"
                },
                "A": {  # 安全阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "2",   # 全启式
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "GA": {  # 杠杆式安全阀默认值
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "2",   # 单杠杆
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "Y": {  # 减压阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接
                    "structure": "1",   # 薄膜式
                    "sealing": "X",
                    "pressure": "16",
                    "material": "T"     # 铜材质
                },
                "S": {  # 蒸汽疏水阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接
                    "structure": "1",   # 浮球式
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "P": {  # 排污阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "X": {  # 旋塞阀默认值
                    "drive_mode": "",
                    "connection": "1",  # 丝口连接
                    "structure": "3",   # 填料密封直通
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                }
            },
            "custom_products": {
                # 用户自定义产品
                "100X": {
                    "name": "遥控浮球阀",
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "200X": {
                    "name": "可调式减压阀",
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "500X": {
                    "name": "泄压/持压阀",
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                },
                "800X": {
                    "name": "缓闭式止回阀",
                    "drive_mode": "",
                    "connection": "4",  # 法兰连接
                    "structure": "1",
                    "sealing": "X",
                    "pressure": "16",
                    "material": "Q"
                }
            }
        }

    # -----------------------------
    # 定价/折扣相关
    # -----------------------------
    def get_user_discount(self, username: str) -> float:
        """获取用户折扣（0-1），默认 1.0"""
        rules = self.load_user_rules(username) or {}
        pricing = rules.get("pricing", {}) or {}
        discount = pricing.get("discount", 1.0)
        try:
            d = float(discount)
            if d <= 0 or not (0 < d <= 1.0):
                return 1.0
            return d
        except Exception:
            return 1.0

    def set_user_discount(self, username: str, discount: float) -> bool:
        """设置用户折扣（0-1），并保存到用户规则文件"""
        try:
            d = float(discount)
            if not (0 < d <= 1.0):
                raise ValueError("discount must be in (0,1]")
            rules = self.load_user_rules(username) or self.get_default_rules()
            pricing = rules.get("pricing") or {}
            pricing["discount"] = d
            rules["pricing"] = pricing
            return self.save_user_rules(username, rules)
        except Exception as e:
            print(f"❌ 设置折扣失败: {e}")
            return False
    
    def get_options_for_frontend(self) -> Dict[str, Any]:
        """获取前端需要的选项数据"""
        return {
            "drive_modes": self.drive_modes,
            "connection_types": self.connection_types,
            "structure_forms": self.structure_forms,
            "sealing_materials": self.sealing_materials,
            "pressure_values": self.pressure_values,
            "body_materials": self.body_materials,
            "basic_product_types": self.basic_product_types
        }
    
    def apply_default_rules(self, username: str, valve_info: Dict[str, Any]) -> Dict[str, Any]:
        """应用默认规则补全阀门信息 - 所有默认数据都从用户的default_rules.json中读取"""
        print(f"🔍 apply_default_rules 被调用: username={username}")
        
        # 确保用户有默认规则文件
        user_rules = self.load_user_rules(username)
        print(f"📋 从用户规则文件加载的规则: {user_rules}")
        
        # 识别产品类型
        product_type = valve_info.get('product_type', '')
        print(f"🏷️  产品类型: {product_type}")
        if not product_type:
            print("❌ 没有产品类型，返回原始信息")
            return valve_info
        
        # 获取默认值 - 只从用户的规则文件中获取
        defaults = None
        if product_type in user_rules.get('product_defaults', {}):
            defaults = user_rules['product_defaults'][product_type]
            print(f"✅ 从用户规则文件找到产品默认规则: {defaults}")
        elif product_type in user_rules.get('custom_products', {}):
            defaults = user_rules['custom_products'][product_type]
            print(f"✅ 从用户规则文件找到自定义产品规则: {defaults}")
        
        if not defaults:
            print(f"❌ 在用户规则文件中没有找到 {product_type} 的默认规则")
            return valve_info
        
        # 应用默认值的优先级策略：
        # 1. 如果用户在规则文件中设置了非空默认值，使用用户设置的值（覆盖系统推断）
        # 2. 如果用户在规则文件中设置为空，且当前值为空，则不处理
        # 3. 如果用户在规则文件中设置为空，且当前值非空，保留当前值
        result = valve_info.copy()
        for key, default_value in defaults.items():
            if key not in ['name', 'product_type']:  # 不处理这些关键字段
                current_value = result.get(key, '')
                
                if default_value:  # 用户在规则文件中设置了非空默认值
                    if current_value != default_value:
                        print(f"🔧 应用用户规则文件中的默认值: {key} = '{current_value}' -> '{default_value}' (用户规则文件优先)")
                        result[key] = default_value
                    else:
                        print(f"✅ 值已匹配用户规则文件设置: {key} = {current_value}")
                else:  # 用户在规则文件中设置为空
                    if not current_value:
                        print(f"⚪ 用户规则文件未设置且当前为空: {key} = '' (保持空值)")
                    else:
                        print(f"✅ 保留系统推断值: {key} = {current_value} (用户规则文件未设置)")
        
        print(f"📋 应用用户规则文件后的最终结果: {result}")
        return result

    def create_interactive_options(self, valve_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建交互式选择选项"""
        product_type = valve_info.get('product_type', '')
        
        options = {
            "drive_modes": self.drive_modes,
            "connection_types": self.connection_types,
            "sealing_materials": self.sealing_materials,
            "pressure_values": self.pressure_values,
            "body_materials": self.body_materials
        }
        
        # 根据产品类型提供对应的结构形式选项
        if product_type in self.structure_forms:
            options["structure_forms"] = self.structure_forms[product_type]
        else:
            options["structure_forms"] = {}
        
        return options