# 闻香记录数仓

一个本地运行的闻香记录系统。前端负责录入、搜索、删除和导出 CSV，后端使用 Python 标准库提供 HTTP API，并将数据写入 SQLite。

## 数据模型

- `dim_sample`：样本维表，保存样本ID、类型、原料名称、学名、品牌/来源。
- `dim_odor_class`：气味分类维表，保存一级分类、二级分类。
- `dim_anchor`：归属锚点维表，用于标准化对比。
- `fact_smell_session`：闻香事实表，保存一次闻香的日期、强度、扩散性、挥发速度和主观评价。
- `bridge_session_keyword`：关键词桥表，支持一条记录对应多个气味关键词。
- `fact_volatility_note`：挥发变化明细事实，保存 0 分钟、10 分钟、30 分钟、2 小时记录。
- `fact_comparison`：对比事实，保存对比样本、差异描述、相对强度、归属锚点。
- `fact_blend_experiment`：组合实验事实，保存配方比例、和谐度、冲突和改进建议。

## 运行

```powershell
$env:PYTHONPATH="$PWD\src"
py -m olfactory_warehouse
```

打开：

```text
http://127.0.0.1:8765
```

默认数据库文件：

```text
data/olfactory_warehouse.sqlite3
```

可通过环境变量覆盖：

```powershell
$env:OLFACTORY_DB_PATH="C:\path\to\olfactory.sqlite3"
$env:OLFACTORY_PORT="8765"
py -m olfactory_warehouse
```

## 校验规则

- 日期必须是 `YYYY-MM-DD`。
- `intensity` 和 `preference_score` 必须是 1-5 的整数。
- `sample_type` 只允许 `单体`、`组合`。
- `diffusion` 只允许 `弱`、`中`、`强`。
- `volatility_speed` 只允许 `快`、`中`、`慢`。
- `relative_intensity` 只允许空、`强`、`弱`、`相近`。
- `harmonious` 只允许空、`是`、`否`、`部分`。
- 文本字段有长度限制，避免异常大内容写入数据库。

## 测试

```powershell
$env:PYTHONPATH="$PWD\src"
py -m unittest discover -s tests
```

## 使用手册

闻香训练流程、每日步骤、字段填写规范和组合实验方法见：

```text
docs/USER_GUIDE.md
```

## WSL 环境

Windows 与 WSL 路径、运行方式、数据库位置差异见：

```text
docs/WSL_SETUP.md
```
