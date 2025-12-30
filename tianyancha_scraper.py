import time
import logging
import re
from datetime import datetime
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from config import SEARCH_URL_TEMPLATE, DATE_FILTER_START, DATE_FILTER_END


logger = logging.getLogger(__name__)


class TianyanchaScraper:
    """天眼查数据爬虫类"""

    def __init__(self, browser_manager):
        """
        初始化爬虫

        Args:
            browser_manager: BrowserManager实例
        """
        self.browser_manager = browser_manager
        self.driver = browser_manager.get_driver()
        self.collected_data = []

    def search_toubiao(self, keyword, max_pages=5, max_items_per_page=20):
        """
        搜索招投标信息（支持分页）

        Args:
            keyword: 搜索关键字
            max_pages: 最大抓取页数，默认5页
            max_items_per_page: 每页最大提取条目数，默认20

        Returns:
            list: 搜索结果列表
        """
        all_results = []
        try:
            # 直接构造并访问带关键词的招投标搜索URL
            search_url = SEARCH_URL_TEMPLATE.format(keyword=quote(keyword))
            logger.info(f"正在搜索关键词: {keyword}")
            logger.info(f"访问URL: {search_url}")

            self.browser_manager.navigate_to(search_url)
            time.sleep(3)

            # 处理可能的弹窗
            self._close_overlays()
            self._wait_for_results()

            # 分页抓取
            for page in range(1, max_pages + 1):
                logger.info(f"正在抓取第 {page}/{max_pages} 页...")

                # 解析当前页
                results = self._parse_search_results_fast(keyword, max_items=max_items_per_page)
                logger.info(f"✓ 第 {page} 页获取到 {len(results)} 条结果")

                all_results.extend(results)

                # 如果没有结果，可能已到最后一页
                if len(results) == 0:
                    logger.info("已无更多结果")
                    break

                # 尝试翻到下一页
                if page < max_pages:
                    if not self._go_to_next_page():
                        logger.info("已到达最后一页")
                        break
                    # 翻页后等待新页面加载完成
                    time.sleep(3)
                    self._wait_for_results(timeout=10)

            logger.info(f"✓ 关键词 '{keyword}' 共获取 {len(all_results)} 条结果")
            return all_results

        except Exception as e:
            logger.error(f"❌ 搜索过程出错: {str(e)}")
            return all_results

    def _parse_search_results(self, keyword):
        """
        解析搜索结果（保留兼容）

        Args:
            keyword: 搜索关键词

        Returns:
            list: 解析后的数据列表
        """
        return self._parse_search_results_fast(keyword)

    def _parse_search_results_fast(self, keyword, max_items=20):
        """
        快速解析搜索结果，直接定位可点击的结果项

        Args:
            keyword: 搜索关键词
            max_items: 最大处理条目数

        Returns:
            list: 解析后的数据列表
        """
        try:
            results = []
            time.sleep(1)

            # 查找所有可点击的结果标题（/bid/ 详情链接）
            result_links = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href,'/bid/')][ancestor::*[contains(@class,'result') or contains(@class,'item') or contains(@class,'list')]]"
            )

            if not result_links:
                # 备用选择器
                result_links = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'result') or contains(@class,'item')]//a[contains(@href,'/bid/')]"
                )

            # 限制数量
            result_links = result_links[:max_items]

            logger.info(f"找到 {len(result_links)} 个可点击的结果项")

            # 收集所有链接URL和名称，避免遍历时元素失效
            links_data = []
            for idx, link in enumerate(result_links[:max_items]):
                try:
                    url = link.get_attribute('href')
                    name = link.text.strip()
                    if url and name:
                        links_data.append({'url': url, 'name': name, 'index': idx + 1})
                except Exception:
                    continue

            # 逐个访问详情页并提取数据（仅抓取正文，不跟随页面内其他链接）
            for data in links_data:
                try:
                    logger.info(f"[{data['index']}/{len(links_data)}] 正在提取: {data['name']}")
                    bid_data = self._extract_bid_from_detail_page(data['url'], data['name'], keyword)
                    if bid_data:  # None表示日期过滤排除
                        results.append(bid_data)
                        logger.info(f"✓ [{data['index']}/{len(links_data)}] 已提取: {data['name']}")
                    time.sleep(0.5)  # 减少延迟提升速度
                except Exception as e:
                    logger.warning(f"⚠ [{data['index']}/{len(links_data)}] 提取失败: {data['name']} - {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"❌ 解析搜索结果时出错: {str(e)}")
            return []

    def _find_search_input_toubiao(self, timeout=10):
        """定位招投标页的搜索输入框，兼容不同结构与 iframe。"""
        try:
            self.driver.switch_to.default_content()
            # 候选定位器更聚焦招投标页
            candidates = [
                (By.XPATH, "//section|//div[.//text()[contains(.,'招投标')]]//input[contains(@placeholder,'关键词') or contains(@placeholder,'关键字') or contains(@placeholder,'项目名称') or contains(@placeholder,'招投标') or @type='search']"),
                (By.XPATH, "//input[@name='keyword' or @name='query' or @name='q']"),
                (By.CSS_SELECTOR, ".search-box input, .toubiao-search input, .tyc-search input, input.search-input")
            ]
            elem = self._find_first(candidates, timeout=timeout)
            if elem and elem.is_displayed():
                return elem

            frames = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for frame in frames:
                try:
                    self.driver.switch_to.frame(frame)
                    elem = self._find_first(candidates, timeout=2, log_failure=False)
                    if elem and elem.is_displayed():
                        return elem
                except Exception:
                    pass
                finally:
                    self.driver.switch_to.default_content()
        except Exception:
            pass
        return None

    def _find_first(self, locator_list, timeout=10, log_failure=True):
        """尝试多个定位器，返回第一个匹配元素。"""
        end = time.time() + timeout
        while time.time() < end:
            for by, value in locator_list:
                try:
                    elem = self.driver.find_element(by, value)
                    return elem
                except Exception:
                    continue
            time.sleep(0.3)
        if log_failure:
            logger.debug(f"未定位到元素 locators={locator_list}")
        return None

    def _close_overlays(self):
        """尝试关闭可能的弹窗/遮罩。"""
        try:
            self.driver.switch_to.default_content()
            candidates = [
                (By.XPATH, "//div[contains(@class,'modal') or contains(@class,'dialog')]//span[contains(@class,'close') or contains(text(),'×')]")
                ,(By.XPATH, "//button[contains(@class,'close') or contains(text(),'关闭')]")
                ,(By.CSS_SELECTOR, ".tyc-modal .close,.modal .close")
            ]
            close_btn = self._find_first(candidates, timeout=2, log_failure=False)
            if close_btn:
                try:
                    self.driver.execute_script("arguments[0].click();", close_btn)
                    time.sleep(0.5)
                except Exception:
                    pass
        except Exception:
            pass

    def _ensure_toubiao_context(self):
        """确保当前处于招投标模块上下文，若有模块切换则点击招投标。"""
        try:
            self.driver.switch_to.default_content()
            # 若页面存在模块导航，点击“招投标”
            tab = self._find_first([
                (By.XPATH, "//*[contains(text(),'招投标') and (self::a or self::span or self::div)]"),
                (By.CSS_SELECTOR, ".tab a, .nav a")
            ], timeout=3, log_failure=False)
            if tab and '招投标' in tab.text:
                try:
                    tab.click()
                    time.sleep(1)
                except Exception:
                    pass
        except Exception:
            pass

    def _wait_for_results(self, timeout=10):
        """等待搜索结果区域出现。"""
        end = time.time() + timeout
        while time.time() < end:
            try:
                elems = self.driver.find_elements(By.XPATH, "//div[contains(@class,'result') or contains(@class,'list') or contains(@class,'item')]")
                if elems:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def _extract_company_info(self, item, keyword):
        """
        提取单个企业信息

        Args:
            item: 单个结果项元素
            keyword: 搜索关键词

        Returns:
            dict: 企业信息字典
        """
        try:
            company_data = {
                "企业名称": "",
                "省份": "",
                "企业经营范围": "",
                "企业地址": "",
                "企业法人": "",
                "企业联系电话": "",
                "成立日期": "",
                "营业期限": "",
                "注册资金": "",
                "统一社会信用代码": "",
                "纳税人识别号": "",
                "实际业务负责人": "",
                "实际联系号码": "",
                "代理产品类别": keyword,
                "微信/邮箱": "",
                "配送省份": "",
                "覆盖地区": "",
                "覆盖医院": ""
            }

            # 如果item是WebElement，转换为字符串处理
            if hasattr(item, 'get_attribute'):
                # 这是WebElement
                try:
                    # 点击查看详情
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    time.sleep(0.5)

                    # 获取企业名称
                    name_elem = item.find_element(By.XPATH, ".//span[@class='company-name'] | .//a[@class='company-link']")
                    if name_elem:
                        company_data["企业名称"] = name_elem.text.strip()

                    # 获取地址信息（用于提取省份）
                    addr_elem = item.find_element(By.XPATH, ".//span[@class='address'] | .//div[@class='location']")
                    if addr_elem:
                        address = addr_elem.text.strip()
                        company_data["企业地址"] = address
                        # 提取省份
                        company_data["省份"] = self._extract_province(address)

                    # 尝试点击查看详情链接以获取更多信息
                    try:
                        detail_link = item.find_element(By.XPATH, ".//a[@class='detail-link' or contains(@href, '/gongshang/')]")
                        detail_link.click()
                        time.sleep(2)

                        # 获取详情页面信息
                        self._extract_detail_page_info(company_data)

                        # 返回搜索结果页面
                        self.driver.back()
                        time.sleep(2)
                    except Exception as e:
                        logger.debug(f"无法获取详情页面: {str(e)}")

                except Exception as e:
                    logger.debug(f"提取WebElement信息失败: {str(e)}")

            return company_data

        except Exception as e:
            logger.debug(f"提取企业信息失败: {str(e)}")
            return None

    def _extract_bid_from_detail_page(self, url, title, keyword):
        """
        直接访问招投标详情页并提取正文（不跟随页面内链接）

        Args:
            url: 招投标详情页URL（/bid/...）
            title: 结果标题
            keyword: 搜索关键词

        Returns:
            dict: 以现有列为键的字典，或None如果不在日期范围内
        """
        data = {
            "企业名称": title,
            "省份": "",
            "企业经营范围": "",
            "企业地址": "",
            "企业法人": "",
            "企业联系电话": "",
            "成立日期": "",
            "营业期限": "",
            "注册资金": "",
            "统一社会信用代码": "",
            "纳税人识别号": "",
            "实际业务负责人": "",
            "实际联系号码": "",
            "代理产品类别": keyword,
            "微信/邮箱": "",
            "配送省份": "",
            "覆盖地区": "",
            "覆盖医院": ""
        }

        try:
            # 新标签打开详情页
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)

            # 尝试提取发布日期（优先处理，用于过滤）
            publish_date = None
            try:
                date_candidates = [
                    (By.XPATH, "//*[contains(text(),'发布日期') or contains(text(),'公告日期') or contains(text(),'发布时间')]/following-sibling::*[1]"),
                    (By.XPATH, "//*[contains(text(),'发布日期') or contains(text(),'公告日期')]/parent::*/following-sibling::*[1]"),
                    (By.XPATH, "//span[contains(@class,'date') or contains(@class,'time')]"),
                    (By.XPATH, "//div[contains(@class,'date') or contains(@class,'time')]"),
                ]
                pub = self._find_first(date_candidates, timeout=3, log_failure=False)
                if pub:
                    date_text = pub.text.strip()
                    data["成立日期"] = date_text
                    publish_date = self._parse_date(date_text)
            except Exception as e:
                logger.debug(f"提取日期失败: {str(e)}")

            # 日期过滤：只保留2020-01-01到2025-11-30的数据
            if publish_date:
                filter_start = datetime.strptime(DATE_FILTER_START, "%Y-%m-%d")
                filter_end = datetime.strptime(DATE_FILTER_END, "%Y-%m-%d")
                if publish_date < filter_start or publish_date > filter_end:
                    logger.info(f"⊘ 跳过（日期{publish_date.strftime('%Y-%m-%d')}不在范围内）: {title}")
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    return None

            # 提取正文内容容器
            candidates = [
                (By.CSS_SELECTOR, ".bid-detail, .article, .content, .detail, .announcement"),
                (By.XPATH, "//div[contains(@class,'bid') or contains(@class,'detail') or contains(@class,'content')]"),
            ]
            container = self._find_first(candidates, timeout=5, log_failure=False)
            text = ""
            if container:
                text = container.text.strip()
            else:
                # 回退到页面整体文本
                try:
                    text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
                except Exception:
                    text = ""

            # 适度裁剪正文长度，避免Excel过长
            if text:
                data["企业经营范围"] = text[:2000]

            # 尝试从内容中提取企业地址和省份
            if text:
                # 查找地址模式
                addr_patterns = [
                    r'地址[：:](.*?)(?:\n|$)',
                    r'联系地址[：:](.*?)(?:\n|$)',
                    r'详细地址[：:](.*?)(?:\n|$)',
                ]
                for pattern in addr_patterns:
                    match = re.search(pattern, text)
                    if match:
                        address = match.group(1).strip()
                        data["企业地址"] = address[:100]  # 限制长度
                        data["省份"] = self._extract_province(address)
                        break

            # 关闭详情页标签并返回
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return data

        except Exception as e:
            logger.debug(f"访问招投标详情失败 {url}: {str(e)}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass
            return data

    def _parse_date(self, date_str):
        """
        解析日期字符串为datetime对象

        Args:
            date_str: 日期字符串

        Returns:
            datetime: 日期对象，解析失败返回None
        """
        if not date_str:
            return None

        # 常见日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y年%m月%d日",
            "%Y/%m/%d",
            "%Y.%m.%d",
        ]

        # 提取日期数字
        date_match = re.search(r'(\d{4})[年/-.]?(\d{1,2})[月/-.]?(\d{1,2})', date_str)
        if date_match:
            try:
                year, month, day = date_match.groups()
                return datetime(int(year), int(month), int(day))
            except Exception:
                pass

        # 尝试标准格式
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except Exception:
                continue

        return None

    def _extract_province(self, address):
        """
        从地址中提取省份

        Args:
            address: 地址字符串

        Returns:
            str: 省份名称
        """
        provinces = [
            "北京", "上海", "天津", "重庆",
            "河北", "山西", "辽宁", "吉林", "黑龙江",
            "江苏", "浙江", "安徽", "福建", "江西", "山东",
            "河南", "湖北", "湖南", "广东", "广西", "海南",
            "四川", "贵州", "云南", "西藏",
            "陕西", "甘肃", "青海", "宁夏", "新疆",
            "台湾", "香港", "澳门"
        ]

        for province in provinces:
            if province in address:
                return province

        return "未知"

    def save_data(self, data_list):
        """
        保存收集的数据

        Args:
            data_list: 数据列表
        """
        self.collected_data.extend(data_list)
        logger.info(f"✓ 已保存 {len(data_list)} 条数据，总计: {len(self.collected_data)} 条")

    def get_collected_data(self):
        """
        获取所有收集的数据

        Returns:
            list: 数据列表
        """
        return self.collected_data

    def _go_to_next_page(self):
        """
        翻到下一页

        Returns:
            bool: 成功返回True，否则False
        """
        try:
            # 查找"下一页"按钮
            next_btns = [
                (By.XPATH, "//a[contains(text(),'下一页') or contains(text(),'下页')]"),
                (By.XPATH, "//button[contains(text(),'下一页') or contains(text(),'下页')]"),
                (By.CSS_SELECTOR, ".pagination .next, .page-next, a[rel='next']"),
                (By.XPATH, "//li[contains(@class,'next')]//a | //span[contains(@class,'next')]//a")
            ]

            next_btn = self._find_first(next_btns, timeout=3, log_failure=False)
            if next_btn:
                # 检查是否禁用
                classes = next_btn.get_attribute('class') or ''
                if 'disabled' in classes or 'inactive' in classes:
                    return False

                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(0.5)
                next_btn.click()
                time.sleep(2)
                self._wait_for_results(timeout=5)
                return True

            return False
        except Exception as e:
            logger.debug(f"翻页失败: {str(e)}")
            return False
