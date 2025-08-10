# 禁用Excel价格自动填充修改说明

## 修改目的

用户要求生成的xlsx文件不要自动填充价格，保持价格列为空，让用户可以手动填入价格。

## 修改内容

### 修改位置
- **文件**：`quote-system/backend/main.py`
- **API端点**：`POST /api/generate-quote`
- **修改行数**：第1333行

### 修改前
```python
auto_fill_price: bool = Form(True)  # 新增参数，是否自动用价格表再次填充价格和品牌
```

### 修改后
```python
auto_fill_price: bool = Form(False)  # 新增参数，是否自动用价格表再次填充价格和品牌
```

## 功能说明

### 相关函数：`match_quote_with_price_table`
这个函数负责：
1. 将生成的报价单与价格表进行匹配
2. 自动填充单价列
3. 根据单价和数量计算总价
4. 填充品牌信息

### 控制逻辑
```python
# 自动用价格表再次填充价格和品牌
if auto_fill_price:
    print(f"[QUOTE] 自动用价格表再次填充价格和品牌...")
    match_quote_with_price_table(standard_xlsx, price_path, brand)
```

现在当 `auto_fill_price=False` 时，系统会：
- 生成包含所有必要列的Excel文件
- **不会**自动填充价格信息
- **不会**自动计算总价
- **不会**自动填充品牌信息
- 保持价格列为空，供用户手动填写

## 使用效果

### 修改前的行为：
- 生成Excel文件时会自动从价格表匹配价格
- 单价列会被自动填充
- 总价会被自动计算
- 品牌信息会被自动设置

### 修改后的行为：
- 生成Excel文件时不会自动填充价格
- 单价列保持为空
- 总价列保持为空  
- 品牌列保持为空
- 用户可以手动在Excel中填写价格信息

## 向后兼容性

- 如果前端需要启用价格自动填充，可以在API调用时设置 `auto_fill_price=true`
- 不影响CSV格式的报价生成（CSV仍然包含多品牌价格信息）
- 不影响其他报价生成功能

## API调用示例

### 禁用价格自动填充（默认）：
```javascript
fetch('/api/generate-quote', {
    method: 'POST',
    body: formData  // auto_fill_price 默认为 false
})
```

### 启用价格自动填充：
```javascript
const formData = new FormData();
formData.append('auto_fill_price', 'true');
// ... 其他参数

fetch('/api/generate-quote', {
    method: 'POST',
    body: formData
})
``` 