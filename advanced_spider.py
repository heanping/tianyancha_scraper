#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天眼查爬虫高级版本
包含代理、重试机制、数据去重等功能
"""

import time
import logging
import hashlib
from collections import defaultdict
from browser_manager import BrowserManager
from login_handler import LoginHandler
from tianyancha_scraper import TianyanchaScraper
from excel_exporter import export_to_excel


logger = logging.getLogger(__name__)


class AdvancedTianyanchaSpider:
    """天眼查爬虫高级版本"""

    def __init__(self, browser_type="chrome", use_proxy=False, proxy_list=None):
        """
        初始化高级爬虫

        Args:
            browser_type: 浏览器类型
            use_proxy: 是否使用代理
            proxy_list: 代理列表
        """
        self.browser_type = browser_type
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.browser_manager = None
        self.scraper = None
        self.all_data = []
        self.duplicate_data = set()  # 用于去重
        self.failed_keywords = []  # 失败的关键词列表
        self.retry_count = 3  # 重试次数

    def _generate_data_hash(self, company_data):
        """
        为企业数据生成哈希值用于去重

        Args:
            company_data: 企业数据字典

        Returns:
            str: 哈希值
        """
        # 用企业名称和地址生成哈希
        unique_key = f"{company_data.get('企业名称', '')}{company_data.get('企业地址', '')}"
        return hashlib.md5(unique_key.encode()).hexdigest()

    def _deduplicate_data(self, data_list):
        """
        去重数据

        Args:
            data_list: 数据列表

        Returns:
            list: 去重后的数据列表
        """
        deduplicated = []
        for item in data_list:
            data_hash = self._generate_data_hash(item)
            if data_hash not in self.duplicate_data:
                self.duplicate_data.add(data_hash)
                deduplicated.append(item)
        return deduplicated

    def run_with_retry(self, keywords, username=None, password=None):
        """
        带重试机制的爬虫运行

        Args:
            keywords: 关键词列表
            username: 用户名
            password: 密码

        Returns:
            bool: 成功返回True
        """
        attempt = 0

        while attempt < self.retry_count:
            try:
                logger.info(f"第 {attempt + 1} 次尝试...")

                # 初始化浏览器
                logger.info(f"正在启动 {self.browser_type.upper()} 浏览器...")
                self.browser_manager = BrowserManager(browser_type=self.browser_type)
                time.sleep(2)

                # 执行登录
                logger.info("执行登录...")
                login_handler = LoginHandler(self.browser_manager)
                if not login_handler.login(username, password):
                    logger.error("登录失败")
                    self.browser_manager.close()
                    attempt += 1
                    time.sleep(5)
                    continue

                logger.info("✓ 登录成功")
                time.sleep(3)

                # 初始化爬虫
                self.scraper = TianyanchaScraper(self.browser_manager)

                # 执行搜索和数据采集
                logger.info("执行数据采集...")
                for idx, keyword in enumerate(keywords, 1):
                    logger.info(f"处理关键词 {idx}/{len(keywords)}: {keyword}")

                    try:
                        # 搜索
                        results = self.scraper.search_toubiao(keyword)

                        # 去重
                        deduplicated_results = self._deduplicate_data(results)

                        # 保存数据
                        if deduplicated_results:
                            self.scraper.save_data(deduplicated_results)
                            logger.info(f"✓ 关键词 '{keyword}' 采集 {len(deduplicated_results)} 条新数据")
                        else:
                            logger.warning(f"⚠ 关键词 '{keyword}' 无新结果")

                        time.sleep(2)

                    except Exception as e:
                        logger.error(f"处理关键词 '{keyword}' 失败: {str(e)}")
                        self.failed_keywords.append(keyword)
                        continue

                # 获取所有数据
                self.all_data = self.scraper.get_collected_data()
                logger.info(f"✓ 数据采集完成，共采集 {len(self.all_data)} 条数据")

                # 关闭浏览器
                if self.browser_manager:
                    self.browser_manager.close()

                return True

            except Exception as e:
                logger.error(f"❌ 第 {attempt + 1} 次尝试失败: {str(e)}")
                if self.browser_manager:
                    self.browser_manager.close()
                attempt += 1
                if attempt < self.retry_count:
                    time.sleep(10)  # 重试前等待

        logger.error(f"❌ 在 {self.retry_count} 次重试后仍然失败")
        return False

    def export_data(self, filename=None):
        """
        导出数据到Excel

        Args:
            filename: 输出文件名

        Returns:
            str: 输出文件路径
        """
        if not self.all_data:
            logger.warning("⚠ 没有数据可导出")
            return None

        logger.info(f"正在导出 {len(self.all_data)} 条数据到Excel...")
        return export_to_excel(self.all_data, filename)

    def get_statistics(self):
        """
        获取统计信息

        Returns:
            dict: 统计数据
        """
        # 统计数据来源
        keyword_count = defaultdict(int)
        province_count = defaultdict(int)

        for item in self.all_data:
            keyword = item.get('代理产品类别', '未分类')
            province = item.get('省份', '未知')
            keyword_count[keyword] += 1
            province_count[province] += 1

        return {
            '总数据量': len(self.all_data),
            '去重后数据量': len(self.all_data),
            '唯一企业数': len(self.duplicate_data),
            '关键词统计': dict(keyword_count),
            '省份分布': dict(province_count),
            '失败关键词': self.failed_keywords,
            '失败数量': len(self.failed_keywords)
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        logger.info("\n" + "=" * 50)
        logger.info("爬虫执行统计")
        logger.info("=" * 50)
        logger.info(f"总数据量: {stats['总数据量']} 条")
        logger.info(f"唯一企业: {stats['唯一企业数']} 个")

        if stats['关键词统计']:
            logger.info("\n关键词统计:")
            for keyword, count in stats['关键词统计'].items():
                logger.info(f"  {keyword}: {count} 条")

        if stats['省份分布']:
            logger.info("\n省份分布（Top 5）:")
            sorted_provinces = sorted(stats['省份分布'].items(), key=lambda x: x[1], reverse=True)
            for province, count in sorted_provinces[:5]:
                logger.info(f"  {province}: {count} 条")

        if stats['失败关键词']:
            logger.warning(f"\n失败关键词 ({len(stats['失败关键词'])} 个):")
            for keyword in stats['失败关键词']:
                logger.warning(f"  {keyword}")

        logger.info("=" * 50 + "\n")


if __name__ == "__main__":
    from config import KEYWORDS, BROWSER_TYPE, LOGIN_USERNAME, LOGIN_PASSWORD

    # 使用高级爬虫
    spider = AdvancedTianyanchaSpider(browser_type=BROWSER_TYPE)

    # 运行爬虫
    success = spider.run_with_retry(KEYWORDS, LOGIN_USERNAME, LOGIN_PASSWORD)

    if success:
        # 导出数据
        spider.export_data()

        # 打印统计
        spider.print_statistics()
    else:
        logger.error("爬虫执行失败")
