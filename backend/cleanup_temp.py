import os
import shutil
import sys

# 设置数据根目录
DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'merchant_data')
print(f'数据根目录: {DATA_ROOT}')

# 检查所有用户目录
for user in os.listdir(DATA_ROOT):
    user_dir = os.path.join(DATA_ROOT, user)
    if os.path.isdir(user_dir):
        print(f'用户目录: {user_dir}')
        
        # 查找临时文件夹
        for item in os.listdir(user_dir):
            item_path = os.path.join(user_dir, item)
            if os.path.isdir(item_path) and ("temp_" in item):
                print(f'发现临时目录: {item_path}')
                print(f'目录内容: {os.listdir(item_path)}')
                
                # 尝试删除
                try:
                    print(f'尝试删除: {item_path}')
                    shutil.rmtree(item_path)
                    print(f'删除成功: {item_path}')
                except Exception as e:
                    print(f'删除失败: {item_path}, 错误: {e}')
                    
                # 检查是否删除成功
                if os.path.exists(item_path):
                    print(f'删除后仍然存在: {item_path}')
                else:
                    print(f'确认已删除: {item_path}') 