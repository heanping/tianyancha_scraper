#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天眼查爬虫主程序
使用说明：
1. 安装依赖: pip install -r requirements.txt
2. 修改config.py中的登录信息（用户名和密码）
3. 运行本脚本: python main.py
"""

import time
import logging
import sys
from datetime import datetime
from browser_manager import BrowserManager
from login_handler import LoginHandler
from tianyancha_scraper import TianyanchaScraper
from excel_exporter import export_to_excel
from config import KEYWORDS, BROWSER_TYPE, OUTPUT_EXCEL_FILE


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TianyanchaSpider:
    """天眼查爬虫主类"""

    def __init__(self, browser_type=BROWSER_TYPE):
        """
        初始化爬虫

        Args:
            browser_type: 浏览器类型
        """
        self.browser_type = browser_type
        self.browser_manager = None
        self.scraper = None
        self.all_data = []

    def run(self):
        """执行爬虫主流程"""
        try:
            logger.info("=" * 50)
            logger.info("天眼查爬虫 v1.0")
            logger.info("=" * 50)

            # 初始化浏览器
            logger.info(f"正在启动 {self.browser_type.upper()} 浏览器...")
            self.browser_manager = BrowserManager(browser_type=self.browser_type)
            time.sleep(2)

            # 等待人工登录
            logger.info("\n【第1步】请在浏览器中人工登录...")
            login_handler = LoginHandler(self.browser_manager)
            if not login_handler.wait_for_manual_login(max_wait_seconds=600):
                logger.error("❌ 未检测到登录成功，程序终止")
                return False

            # 初始化爬虫
            self.scraper = TianyanchaScraper(self.browser_manager)

            # 执行搜索和数据采集
            logger.info("【第2步】执行关键字搜索和数据采集...\n")
            for idx, keyword in enumerate(KEYWORDS, 1):
                logger.info(f"正在处理关键词 {idx}/{len(KEYWORDS)}: {keyword}")

                try:
                    # 搜索
                    results = self.scraper.search_toubiao(keyword)

                    # 保存数据
                    if results:
                        self.scraper.save_data(results)
                        logger.info(f"✓ 关键词 '{keyword}' 采集完成，共 {len(results)} 条\n")
                    else:
                        logger.warning(f"⚠ 关键词 '{keyword}' 无结果\n")

                    time.sleep(2)  # 关键词之间的延迟

                except Exception as e:
                    logger.error(f"❌ 处理关键词 '{keyword}' 失败: {str(e)}")
                    continue

            # 获取所有数据
            self.all_data = self.scraper.get_collected_data()
            logger.info(f"\n✓ 数据采集完成，共采集 {len(self.all_data)} 条数据")

            # 导出Excel
            if self.all_data:
                logger.info("\n【第3步】导出Excel文件...")
                output_file = export_to_excel(self.all_data, OUTPUT_EXCEL_FILE)
                logger.info(f"✓ Excel文件已导出: {output_file}\n")
            else:
                logger.warning("⚠ 未采集到任何数据")

            # 完成
            logger.info("=" * 50)
            logger.info("爬虫执行完成")
            logger.info("=" * 50)
            return True

        except Exception as e:
            logger.error(f"❌ 爬虫执行出错: {str(e)}")
            return False

        finally:
            # 关闭浏览器
            if self.browser_manager:
                logger.info("\n正在关闭浏览器...")
                self.browser_manager.close()


def main():
    """主函数"""

    # 强制使用 Edge 浏览器
    browser_type = 'edge'
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg != 'edge':
            logger.warning(f"仅支持 edge 浏览器，忽略参数: {arg}")
    logger.info("使用浏览器: edge")

    # 创建爬虫实例并运行
    spider = TianyanchaSpider(browser_type=browser_type)
    success = spider.run()

    # 返回退出码
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
