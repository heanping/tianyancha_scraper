# 天眼查爬虫配置文件

# 登录信息
LOGIN_USERNAME = "1336xxxxxxx"  # 替换为你的天眼查账号
LOGIN_PASSWORD = "***********"  # 替换为你的密码

# 网站URL
BASE_URL = "https://www.tianyancha.com"
LOGIN_URL = "https://www.tianyancha.com/login"
SEARCH_URL_TEMPLATE = "https://www.tianyancha.com/s/toubiao/detail?key={keyword}"

# 搜索关键字
KEYWORDS = [
    "生长激素",
    "注射笔",
    "骨龄仪器",
    "蒲地蓝消炎口服液",
    "济川药业"  # 蒲地蓝消炎口服液的生产厂家
]

# 时间过滤配置
DATE_FILTER_START = "2020-01-01"  # 开始日期
DATE_FILTER_END = "2025-11-30"    # 结束日期

# 浏览器配置
BROWSER_TYPE = "edge"  # 可选: chrome, edge
HEADLESS_MODE = False  # True表示无头模式，False表示有界面
IMPLICIT_WAIT_TIME = 10  # 隐式等待时间（秒）
PAGE_LOAD_TIMEOUT = 30  # 页面加载超时时间（秒）

# 输出配置
OUTPUT_EXCEL_FILE = "天眼查招投标数据.xlsx"
OUTPUT_FOLDER = "output"

# 数据字段
OUTPUT_COLUMNS = [
    "企业名称",
    "省份",
    "企业经营范围",
    "企业地址",
    "企业法人",
    "企业联系电话",
    "成立日期",
    "营业期限",
    "注册资金",
    "统一社会信用代码",
    "纳税人识别号",
    "实际业务负责人",
    "实际联系号码",
    "代理产品类别",
    "微信/邮箱",
    "配送省份",
    "覆盖地区",
    "覆盖医院"
]
