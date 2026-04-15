"""
登录页面对象 (Page Object) - 优化版
使用更稳定的定位策略
"""

from playwright.sync_api import Page
from page_objects.base_page import BasePage
from config.settings import MOCK_API_URL


class LoginPage(BasePage):
    """登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 使用语义化定位 + 备用定位器
        self.username_input = page.get_by_placeholder("用户名")
        self.password_input = page.get_by_placeholder("密码")
        self.login_button = page.get_by_role("button", name="登 录")
        self.error_message = page.locator("#error-msg")

    def navigate(self, base_url: str = MOCK_API_URL):
        """导航到登录页面"""
        self.navigate_to(f"{base_url}/login-page")

    def fill_username(self, username: str):
        """填写用户名"""
        self.username_input.fill(username)

    def fill_password(self, password: str):
        """填写密码"""
        self.password_input.fill(password)

    def click_login(self):
        """点击登录按钮"""
        self.login_button.click()

    def login(self, username: str, password: str):
        """
        执行完整登录操作
        """
        self.fill_username(username)
        self.fill_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        """获取错误提示信息"""
        try:
            self.error_message.wait_for(state="visible", timeout=3000)
            return self.error_message.text_content() or ""
        except:
            return ""

    def is_login_success(self) -> bool:
        """判断登录是否成功（等待URL跳转）"""
        try:
            self.wait_for_navigation(url_pattern="**/employee-page", timeout=5000)
            return True
        except:
            return False

    def is_error_displayed(self) -> bool:
        """判断是否显示了错误信息"""
        return self.is_visible("#error-msg", timeout=2000)