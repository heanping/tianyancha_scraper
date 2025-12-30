import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from browser_manager import BrowserManager
from config import LOGIN_URL, LOGIN_USERNAME, LOGIN_PASSWORD


logger = logging.getLogger(__name__)


class LoginHandler:
    """天眼查登录处理器"""

    def __init__(self, browser_manager):
        """
        初始化登录处理器

        Args:
            browser_manager: BrowserManager实例
        """
        self.browser_manager = browser_manager
        self.driver = browser_manager.get_driver()

    def login(self, username=None, password=None):
        """
        执行登录操作

        Args:
            username: 用户名
            password: 密码

        Returns:
            bool: 登录成功返回True，失败返回False
        """
        username = username or LOGIN_USERNAME
        password = password or LOGIN_PASSWORD

        try:
            # 导航到登录页面
            self.browser_manager.navigate_to(LOGIN_URL)
            time.sleep(2)

            logger.info("正在执行登录...")

            # 如果存在登录 iframe，切换到登录 iframe 内
            self._switch_to_login_frame()

            # 切换到密码登录（如果存在“密码登录”选项卡）
            try:
                pwd_tab = self.browser_manager.wait_for_clickable(
                    By.XPATH,
                    "//*[contains(text(),'密码登录') or contains(text(),'账号密码登录') or contains(text(),'账户登录')]",
                    timeout=8
                )
                if pwd_tab:
                    pwd_tab.click()
                    logger.info("✓ 已切换到密码登录模式")
                    time.sleep(1)
            except Exception:
                logger.debug("未找到密码登录切换，继续尝试输入")

            # 查找并填充用户名/邮箱字段
            username_field = self._find_first(
                [
                    (By.XPATH, "//input[@placeholder='请输入登录账号/邮箱/手机号' or @placeholder='账号/邮箱/手机号' or @name='account' or @name='mobile' or @type='tel']"),
                    (By.CSS_SELECTOR, "input[name='account'],input[name='mobile'],input[type='tel'],input[autocomplete='username'],input[inputmode='tel']"),
                ],
                timeout=15
            )

            if username_field:
                username_field.clear()
                username_field.send_keys(username)
                logger.info("✓ 用户名已输入")
                time.sleep(1)
            else:
                logger.error("❌ 未找到用户名输入框")
                return False

            # 查找并填充密码字段
            password_field = self._find_first(
                [
                    (By.XPATH, "//input[@placeholder='请输入登录密码' or @placeholder='密码' or @type='password' or @name='password']"),
                    (By.CSS_SELECTOR, "input[type='password'],input[name='password'],input[autocomplete='current-password']"),
                ],
                timeout=15
            )

            if password_field:
                password_field.clear()
                password_field.send_keys(password)
                logger.info("✓ 密码已输入")
                time.sleep(1)
            else:
                logger.error("❌ 未找到密码输入框")
                return False

            # 勾选“我已阅读并同意”复选框（若存在）
            try:
                agree_box = self.browser_manager.wait_for_clickable(
                    By.XPATH,
                    "//input[@type='checkbox' and (../*[contains(text(),'我已阅读') or contains(text(),'同意')])]/ancestor::label|//label[contains(.,'我已阅读') or contains(.,'同意')]//input[@type='checkbox']",
                    timeout=6
                )
                if agree_box and not agree_box.is_selected():
                    agree_box.click()
                    logger.info("✓ 已勾选同意条款")
                    time.sleep(0.3)
            except Exception:
                logger.debug("未找到同意条款复选框，跳过")

            # 查找并点击登录按钮
            login_button = self.browser_manager.wait_for_clickable(
                By.XPATH,
                "//button[contains(text(), '登录') or contains(text(), '确定') or @class*='login']",
                timeout=15
            )

            if login_button:
                # 滚动到按钮
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(0.5)
                login_button.click()
                logger.info("✓ 登录按钮已点击")
            else:
                logger.error("❌ 未找到登录按钮")
                return False

            # 等待登录完成
            time.sleep(5)

            # 检查是否登录成功
            if self._check_login_success():
                logger.info("✓ 登录成功")
                return True
            else:
                logger.warning("⚠ 登录可能失败，请检查")
                return False

        except Exception as e:
            logger.error(f"❌ 登录过程出错: {str(e)}")
            return False

    def _check_login_success(self):
        """
        检查是否登录成功

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            # 检查是否出现用户信息或首页特征
            # 方法1: 检查个人资料入口
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), '个人资料')]")
                return True
            except:
                pass

            # 方法2: 检查搜索框（登录后主页的特征）
            try:
                self.driver.find_element(By.XPATH, "//input[@placeholder='请输入企业名称、关键词等']")
                return True
            except:
                pass

            # 方法3: 检查URL变化
            current_url = self.driver.current_url
            if "login" not in current_url:
                return True

            # 方法4: 检查是否有错误提示
            try:
                error_message = self.driver.find_element(By.XPATH, "//*[contains(text(), '账号或密码')]")
                if error_message:
                    logger.error(f"❌ 登录错误: {error_message.text}")
                    return False
            except:
                pass

            return False

        except Exception as e:
            logger.error(f"❌ 检查登录状态时出错: {str(e)}")
            return False

    def _switch_to_login_frame(self):
        """尝试切换到包含登录表单的 iframe（如果存在）。"""
        try:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, frame in enumerate(frames):
                try:
                    self.driver.switch_to.frame(frame)
                    # 粗略检查是否存在账号输入框
                    if self._find_first([
                        (By.CSS_SELECTOR, "input[name='account'],input[name='mobile'],input[type='tel'],input[autocomplete='username']"),
                        (By.XPATH, "//input[@type='password']")
                    ], timeout=2, log_failure=False):
                        logger.info(f"✓ 已切换到登录iframe (index {idx})")
                        return True
                except Exception:
                    self.driver.switch_to.default_content()
                    continue
                self.driver.switch_to.default_content()
            # 未找到合适的 iframe 则保持默认内容
            self.driver.switch_to.default_content()
        except Exception as e:
            logger.debug(f"切换登录 iframe 失败: {e}")
            self.driver.switch_to.default_content()
        return False

    def _find_first(self, locator_list, timeout=10, log_failure=True):
        """尝试多个定位器，返回第一个找到的元素。"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            for by, value in locator_list:
                try:
                    elem = self.driver.find_element(by, value)
                    return elem
                except Exception:
                    continue
            time.sleep(0.3)
        if log_failure:
            logger.debug(f"未匹配到元素，locators={locator_list}")
        return None

    def wait_for_manual_login(self, max_wait_seconds=600):
        """打开登录页并等待人工登录完成。

        Args:
            max_wait_seconds: 最大等待秒数，默认 10 分钟。

        Returns:
            bool: 检测到登录成功返回 True，否则 False。
        """
        try:
            from config import LOGIN_URL  # 避免循环导入
            logger.info("请在打开的浏览器中完成登录（支持扫码/密码）。")
            self.browser_manager.navigate_to(LOGIN_URL)
            start = time.time()
            # 循环检测登录状态
            while time.time() - start < max_wait_seconds:
                if self._check_login_success():
                    logger.info("✓ 检测到已登录")
                    return True
                time.sleep(2)
            logger.error("❌ 等待人工登录超时")
            return False
        except Exception as e:
            logger.error(f"❌ 人工登录等待过程出错: {e}")
            return False
