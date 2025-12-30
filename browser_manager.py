import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import BROWSER_TYPE, HEADLESS_MODE, IMPLICIT_WAIT_TIME, PAGE_LOAD_TIMEOUT


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrowserManager:
    """浏览器管理器类"""

    def __init__(self, browser_type=BROWSER_TYPE, headless=HEADLESS_MODE):
        """
        初始化浏览器管理器

        Args:
            browser_type: 浏览器类型（仅支持 'edge'）
            headless: 是否使用无头模式
        """
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.driver = None
        self._init_driver()

    def _init_driver(self):
        """初始化WebDriver"""
        try:
            if self.browser_type == "edge":
                self.driver = self._create_edge_driver()
                logger.info("✓ Edge浏览器已启动")
            else:
                logger.warning(f"仅支持 Edge 浏览器，已强制使用 Edge (收到: {self.browser_type})")
                self.driver = self._create_edge_driver()
                logger.info("✓ Edge浏览器已启动")

            # 设置超时
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(IMPLICIT_WAIT_TIME)

        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {str(e)}")
            raise

    # 移除 Chrome 支持：仅保留 Edge

    def _create_edge_driver(self):
        """创建Edge浏览器驱动"""
        options = webdriver.EdgeOptions()

        # 禁用自动化特征
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 设置用户代理
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')

        if self.headless:
            options.add_argument('--headless=new')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 优先尝试使用 Selenium Manager（无需显式驱动路径）
        try:
            # 如果提供了本地驱动路径，优先使用本地驱动（离线环境）
            local_path = os.environ.get('EDGE_DRIVER_PATH')
            if local_path and os.path.exists(local_path):
                service = EdgeService(local_path)
                return webdriver.Edge(service=service, options=options)

            return webdriver.Edge(options=options)
        except Exception as e:
            logger.warning(f"Selenium Manager 初始化 Edge 失败，回退到 webdriver-manager: {e}")

            # 回退到 webdriver-manager（需要网络以下载驱动）
            try:
                service = EdgeService(EdgeChromiumDriverManager().install())
                return webdriver.Edge(service=service, options=options)
            except Exception as e2:
                logger.error(f"Edge 驱动初始化失败（可能网络不可用或未安装本地驱动）。可设置环境变量 EDGE_DRIVER_PATH 指向本地驱动文件。错误: {e2}")
                raise

    def get_driver(self):
        """获取WebDriver实例"""
        return self.driver

    def navigate_to(self, url):
        """导航到指定URL"""
        try:
            logger.info(f"正在访问: {url}")
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            return True
        except Exception as e:
            logger.error(f"❌ 访问URL失败: {str(e)}")
            return False

    def wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except Exception as e:
            logger.error(f"❌ 元素等待超时: {str(e)}")
            return None

    def wait_for_clickable(self, by, value, timeout=10):
        """等待元素可点击"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except Exception as e:
            logger.error(f"❌ 元素点击超时: {str(e)}")
            return None

    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("✓ 浏览器已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭浏览器失败: {str(e)}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
