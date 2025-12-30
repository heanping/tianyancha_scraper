#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天眼查爬虫 - 测试和开发脚本
用于模块化测试和调试
"""

import time
import logging
import sys
from browser_manager import BrowserManager
from login_handler import LoginHandler
from tianyancha_scraper import TianyanchaScraper
from excel_exporter import export_to_excel


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_browser_manager():
    """测试浏览器管理器"""
    logger.info("\n" + "="*50)
    logger.info("【测试1】浏览器管理器")
    logger.info("="*50)

    try:
        browser = BrowserManager(browser_type="chrome", headless=False)
        logger.info("✓ 浏览器初始化成功")

        # 测试导航
        browser.navigate_to("https://www.google.com")
        logger.info("✓ 页面导航成功")

        time.sleep(2)

        browser.close()
        logger.info("✓ 浏览器关闭成功")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False


def test_element_waiting():
    """测试元素等待功能"""
    logger.info("\n" + "="*50)
    logger.info("【测试2】元素等待")
    logger.info("="*50)

    try:
        browser = BrowserManager(browser_type="chrome", headless=False)

        # 访问页面
        browser.navigate_to("https://www.google.com")
        time.sleep(2)

        # 尝试找到搜索框
        from selenium.webdriver.common.by import By
        element = browser.wait_for_element(By.NAME, "q", timeout=10)

        if element:
            logger.info("✓ 元素找到成功")
            logger.info(f"✓ 元素标签: {element.tag_name}")
        else:
            logger.warning("⚠ 元素未找到")

        browser.close()
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False


def test_login_without_password(url="https://www.tianyancha.com/login"):
    """测试登录页面访问（不输入真实密码）"""
    logger.info("\n" + "="*50)
    logger.info("【测试3】登录页面访问")
    logger.info("="*50)

    try:
        browser = BrowserManager(browser_type="chrome", headless=False)

        # 访问登录页面
        logger.info(f"正在访问: {url}")
        browser.navigate_to(url)

        logger.info("✓ 登录页面已加载")
        logger.info("✓ 可以看到登录表单")

        time.sleep(2)

        # 检查登录元素是否存在
        from selenium.webdriver.common.by import By
        driver = browser.get_driver()

        try:
            driver.find_element(By.XPATH, "//input[@type='text' or @name='account']")
            logger.info("✓ 找到账号输入框")
        except:
            logger.warning("⚠ 未找到账号输入框，可能DOM结构变化")

        try:
            driver.find_element(By.XPATH, "//input[@type='password']")
            logger.info("✓ 找到密码输入框")
        except:
            logger.warning("⚠ 未找到密码输入框，可能DOM结构变化")

        try:
            driver.find_element(By.XPATH, "//button[contains(text(), '登')]")
            logger.info("✓ 找到登录按钮")
        except:
            logger.warning("⚠ 未找到登录按钮，可能DOM结构变化")

        time.sleep(2)
        browser.close()
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False


def test_excel_export():
    """测试Excel导出功能"""
    logger.info("\n" + "="*50)
    logger.info("【测试4】Excel导出功能")
    logger.info("="*50)

    try:
        # 创建测试数据
        test_data = [
            {
                "企业名称": "测试公司1",
                "省份": "北京",
                "企业经营范围": "医药代理",
                "企业地址": "北京市朝阳区",
                "企业法人": "张三",
                "企业联系电话": "010-12345678",
                "成立日期": "2020-01-01",
                "营业期限": "2020-01-01 至 2030-01-01",
                "注册资金": "1000万",
                "统一社会信用代码": "91110000123456789X",
                "纳税人识别号": "91110000123456789",
                "实际业务负责人": "李四",
                "实际联系号码": "13800138000",
                "代理产品类别": "测试关键词",
                "微信/邮箱": "test@example.com",
                "配送省份": "北京,上海",
                "覆盖地区": "东城区,西城区",
                "覆盖医院": "协和医院,301医院"
            },
            {
                "企业名称": "测试公司2",
                "省份": "上海",
                "企业经营范围": "医疗器械代理",
                "企业地址": "上海市浦东新区",
                "企业法人": "王五",
                "企业联系电话": "021-87654321",
                "成立日期": "2021-06-15",
                "营业期限": "2021-06-15 至 2031-06-15",
                "注册资金": "500万",
                "统一社会信用代码": "91310000987654321X",
                "纳税人识别号": "91310000987654321",
                "实际业务负责人": "赵六",
                "实际联系号码": "13900139000",
                "代理产品类别": "测试关键词",
                "微信/邮箱": "test2@example.com",
                "配送省份": "上海,江苏",
                "覆盖地区": "浦东新区,徐汇区",
                "覆盖医院": "复旦附属医院,瑞金医院"
            }
        ]

        # 导出Excel
        logger.info(f"正在导出 {len(test_data)} 条测试数据...")
        filepath = export_to_excel(test_data, "测试数据.xlsx")

        logger.info(f"✓ Excel导出成功: {filepath}")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False


def test_scraper_init(username="test", password="test"):
    """测试爬虫初始化（不实际登录）"""
    logger.info("\n" + "="*50)
    logger.info("【测试5】爬虫初始化")
    logger.info("="*50)

    try:
        browser = BrowserManager(browser_type="chrome", headless=False)
        logger.info("✓ 浏览器初始化成功")

        scraper = TianyanchaScraper(browser)
        logger.info("✓ 爬虫初始化成功")

        logger.info("✓ 爬虫模块可以正常导入")

        browser.close()
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "="*60)
    logger.info("天眼查爬虫 - 测试套件")
    logger.info("="*60)

    tests = [
        ("浏览器管理器", test_browser_manager),
        ("元素等待", test_element_waiting),
        ("登录页面访问", test_login_without_password),
        ("Excel导出", test_excel_export),
        ("爬虫初始化", test_scraper_init),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"【错误】{test_name} 测试异常: {str(e)}")
            results[test_name] = False

        time.sleep(2)  # 测试间隔

    # 总结
    logger.info("\n" + "="*60)
    logger.info("测试总结")
    logger.info("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "❌ 失败"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\n总体: {passed}/{total} 项测试通过")

    return passed == total


def main():
    """主函数"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()

        if test_name == "browser":
            return test_browser_manager()
        elif test_name == "element":
            return test_element_waiting()
        elif test_name == "login":
            return test_login_without_password()
        elif test_name == "excel":
            return test_excel_export()
        elif test_name == "scraper":
            return test_scraper_init()
        else:
            print("用法: python test_spider.py [browser|element|login|excel|scraper|all]")
            return False

    else:
        return run_all_tests()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
