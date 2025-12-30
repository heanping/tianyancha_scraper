# 天眼查招投标爬虫（Edge 版）

抓取天眼查招投标搜索结果（/bid/详情页），应用时间过滤并导出到 Excel。

## 主要特性

- Edge 浏览器单一支持（Selenium Manager 或本地 `msedgedriver`）
- 手动登录后自动按多关键词爬取
- 直接访问招投标搜索 URL，逐页分页抓取
- 仅点击结果标题进入详情，提取正文并日期过滤（2020-01-01 至 2025-11-30）
- Excel 输出包含大标题 + 列头，符合示例格式

## 目录结构

```
tianyancha_new/
├── main.py               # 入口，串起登录等待与爬取
├── config.py             # 配置：关键词、时间范围、输出文件等
├── browser_manager.py    # Edge 浏览器管理
├── login_handler.py      # 手动登录等待逻辑
├── tianyancha_scraper.py # 招投标爬取与详情提取
├── excel_exporter.py     # Excel 导出（标题行 + 列头行）
├── requirements.txt      # 依赖
└── output/               # 输出目录（自动创建）
```

## 环境准备

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```

## 配置（`config.py`）

- `KEYWORDS`: 关键词列表（已包含 “蒲地蓝消炎口服液” 与 “济川药业”）
- `DATE_FILTER_START` / `DATE_FILTER_END`: 日期过滤范围，默认 `2020-01-01` 到 `2025-11-30`
- `HEADLESS_MODE`: 默认 False，推荐保留有界面便于登录
- `OUTPUT_EXCEL_FILE`: Excel 文件名，默认 `天眼查招投标数据.xlsx`

示例：

```python
KEYWORDS = [
    "生长激素",
    "注射笔",
    "骨龄仪器",
    "蒲地蓝消炎口服液",
    "济川药业"
]
DATE_FILTER_START = "2020-01-01"
DATE_FILTER_END = "2025-11-30"
```

## 运行方式

```bash
bash run.sh  # 自动使用 Edge 与 .venv
# 或
python main.py
```

运行后：
1) 浏览器打开天眼查，请手动完成登录；
2) 登录成功后程序会自动按关键词逐页抓取；
3) 结果写入 `output/天眼查招投标数据.xlsx`。

## 输出格式（Excel）

- 第 1 行：`全国内分泌配送商联系表`（合并单元格，大标题）
- 第 2 行：列头（企业名称、省份、企业经营范围、企业地址、企业法人、企业联系电话、成立日期、营业期限、注册资金、统一社会信用代码、纳税人识别号、实际业务负责人、实际联系号码、代理产品类别、微信/邮箱、配送省份、覆盖地区、覆盖医院）
- 第 3 行起：数据行

字段映射要点：
- “企业名称”：搜索结果标题
- “企业经营范围”：详情正文（截断至约 2000 字符）
- “企业地址”：从详情正文尝试提取的地址（若未提取则留空）
- “成立日期”：详情页发布日期/公告日期，且会执行日期范围过滤
- “代理产品类别”：对应搜索关键词

## 运行提示

- 必须登录后再开始抓取；若登录超时请手动刷新/重登再继续。
- 每页默认抓取最多 20 条后翻页，直到用尽页数或无结果。
- 仅点击 `/bid/` 详情链接，不跟随详情页内部其他链接。

## 注意事项

- 本项目仅供学习与内部测试，请遵守目标网站的使用条款与法律法规。
- 若网络受限可在环境变量中提供 `EDGE_DRIVER_PATH` 指向本地 `msedgedriver`。

**最后更新**: 2025-12-30
