#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天眼查爬虫环境检查脚本
用于验证依赖和配置是否正确
"""

import sys
import os
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """检查Python版本"""
    logger.info("【检查1】Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        logger.info(f"✓ Python版本: {version.major}.{version.minor}.{version.micro} (符合要求)")
        return True
    else:
        logger.error(f"❌ Python版本过低: {version.major}.{version.minor} (需要3.7或更高)")
        return False


def check_dependencies():
    """检查依赖包"""
    logger.info("\n【检查2】依赖包...")

    required_packages = {
        'selenium': '4.0+',
        'bs4': '4.9+',
        'openpyxl': '3.0+',
        'webdriver_manager': '3.0+',
        'requests': '2.25+',
    }

    all_ok = True

    for package_name, version_req in required_packages.items():
        try:
            if package_name == 'bs4':
                import bs4
                module_name = 'beautifulsoup4'
            elif package_name == 'webdriver_manager':
                import webdriver_manager
                module_name = 'webdriver-manager'
            else:
                module_name = package_name
                __import__(package_name)

            logger.info(f"✓ {module_name} (已安装)")
        except ImportError:
            logger.error(f"❌ {package_name} (未安装，需要版本 {version_req})")
            all_ok = False

    return all_ok


def check_config():
    """检查配置文件"""
    logger.info("\n【检查3】配置文件...")

    if not os.path.exists('config.py'):
        logger.error("❌ config.py 文件不存在")
        return False

    try:
        import config

        # 检查必需的配置
        required_configs = [
            'LOGIN_USERNAME',
            'LOGIN_PASSWORD',
            'KEYWORDS',
            'BROWSER_TYPE'
        ]

        all_ok = True
        for config_name in required_configs:
            if hasattr(config, config_name):
                value = getattr(config, config_name)

                # 检查是否为默认值
                if config_name == 'LOGIN_USERNAME' and value == 'your_username':
                    logger.warning(f"⚠ {config_name} = {value} (需要修改)")
                elif config_name == 'LOGIN_PASSWORD' and value == 'your_password':
                    logger.warning(f"⚠ {config_name} = {value} (需要修改)")
                else:
                    logger.info(f"✓ {config_name} (已配置)")
            else:
                logger.error(f"❌ 缺少配置: {config_name}")
                all_ok = False

        return all_ok

    except Exception as e:
        logger.error(f"❌ config.py 读取失败: {str(e)}")
        return False


def check_browser_drivers():
    """检查浏览器驱动"""
    logger.info("\n【检查4】浏览器驱动...")

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.microsoft import EdgeChromiumDriverManager

        logger.info("✓ ChromeDriver 管理器 (已安装)")
        logger.info("✓ EdgeDriver 管理器 (已安装)")

        # 尝试初始化驱动
        try:
            chrome_path = ChromeDriverManager().install()
            logger.info(f"✓ ChromeDriver 路径: {chrome_path}")
        except Exception as e:
            logger.warning(f"⚠ ChromeDriver 初始化: {str(e)}")

        try:
            edge_path = EdgeChromiumDriverManager().install()
            logger.info(f"✓ EdgeDriver 路径: {edge_path}")
        except Exception as e:
            logger.warning(f"⚠ EdgeDriver 初始化: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"❌ 浏览器驱动检查失败: {str(e)}")
        return False


def check_output_folder():
    """检查输出文件夹"""
    logger.info("\n【检查5】输出文件夹...")

    output_folder = 'output'
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
            logger.info(f"✓ 已创建输出文件夹: {output_folder}")
        except Exception as e:
            logger.error(f"❌ 创建输出文件夹失败: {str(e)}")
            return False
    else:
        logger.info(f"✓ 输出文件夹存在: {output_folder}")

    return True


def test_import_modules():
    """测试导入模块"""
    logger.info("\n【检查6】模块导入测试...")

    try:
        logger.info("尝试导入 browser_manager...")
        from browser_manager import BrowserManager
        logger.info("✓ browser_manager 导入成功")

        logger.info("尝试导入 login_handler...")
        from login_handler import LoginHandler
        logger.info("✓ login_handler 导入成功")

        logger.info("尝试导入 tianyancha_scraper...")
        from tianyancha_scraper import TianyanchaScraper
        logger.info("✓ tianyancha_scraper 导入成功")

        logger.info("尝试导入 excel_exporter...")
        from excel_exporter import export_to_excel
        logger.info("✓ excel_exporter 导入成功")

        return True

    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {str(e)}")
        return False


def main():
    """主检查函数"""
    logger.info("=" * 50)
    logger.info("天眼查爬虫环境检查")
    logger.info("=" * 50 + "\n")

    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("配置文件", check_config),
        ("浏览器驱动", check_browser_drivers),
        ("输出文件夹", check_output_folder),
        ("模块导入", test_import_modules),
    ]

    results = {}

    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"❌ {check_name} 检查异常: {str(e)}")
            results[check_name] = False

    # 总结
    logger.info("\n" + "=" * 50)
    logger.info("检查总结")
    logger.info("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, result in results.items():
        status = "✓ 通过" if result else "❌ 失败"
        logger.info(f"{status}: {check_name}")

    logger.info(f"\n总体: {passed}/{total} 项检查通过")

    if passed == total:
        logger.info("\n✓ 环境检查完成，所有检查都通过！")
        logger.info("可以运行: python main.py")
        return 0
    elif passed >= total - 1:
        logger.warning("\n⚠ 部分检查未通过，但可能不影响运行")
        logger.warning("请检查上面的警告信息，然后尝试运行: python main.py")
        return 1
    else:
        logger.error("\n❌ 环境检查失败，无法运行爬虫")
        logger.error("请先安装依赖: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
