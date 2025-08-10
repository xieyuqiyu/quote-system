# NaN值JSON序列化修复说明

## 问题描述

在获取价格表内容的API中出现了JSON序列化错误：

```
❌ [ERROR] 获取价格表内容失败: Out of range float values are not JSON compliant: nan
```

## 问题原因

当价格表中包含空值（NaN）时，pandas的DataFrame会将这些值表示为`float('nan')`。虽然Python的标准`json.dumps()`可以处理这些值，但FastAPI的`JSONResponse`更加严格，会拒绝序列化包含NaN的数据，因为NaN不符合JSON标准。

## 修复方案

### 修改前的代码：
```python
# 读取Excel文件
df = pd.read_excel(file_path)

# 转换为字典格式（会包含NaN值）
data = {
    "columns": df.columns.tolist(),
    "data": df.values.tolist(),  # 这里可能包含NaN值
    "total_rows": len(df),
    "total_columns": len(df.columns)
}

return JSONResponse(content=data)  # 会报错：Out of range float values are not JSON compliant
```

### 修改后的代码：
```python
# 读取Excel文件
df = pd.read_excel(file_path)

# 处理NaN值，将其替换为None，以便JSON序列化
df_cleaned = df.where(pd.notna(df), None)

# 转换为字典格式
data = {
    "columns": df_cleaned.columns.tolist(),
    "data": df_cleaned.values.tolist(),  # NaN已被替换为None
    "total_rows": len(df_cleaned),
    "total_columns": len(df_cleaned.columns)
}

return JSONResponse(content=data)  # 正常工作
```

## 技术细节

1. **`df.where(pd.notna(df), None)`**：将DataFrame中的NaN值替换为Python的None
2. **None vs NaN**：Python的None可以正确序列化为JSON的`null`
3. **JSON兼容性**：修复后的数据完全符合JSON标准

## 修复位置

- **文件**：`quote-system/backend/main.py`
- **API端点**：`GET /api/price-table/{filename}`
- **函数**：`get_price_table_content`

## 测试验证

修复后的API能够正确处理包含空值的Excel文件，将NaN值转换为JSON的`null`值，确保前端能够正常接收和处理数据。

## 影响范围

- 修复了价格表查看功能中的JSON序列化错误
- 不影响其他功能，向后兼容
- 提高了系统的稳定性和用户体验 