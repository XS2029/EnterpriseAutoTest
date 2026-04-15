"""
登录页面 UI 自动化测试用例
基于 Page Object 模式
"""

import pytest
from playwright.sync_api import Page
from page_objects.login_page import LoginPage
from config.settings import MOCK_API_URL

BASE_URL = MOCK_API_URL


class TestLoginUI:
    """登录页面测试类"""

    def test_login_success(self, page: Page):
        """
        正向用例：使用正确的用户名和密码登录
        """
        # 1. 初始化页面对象
        login_page = LoginPage(page)
        login_page.navigate(BASE_URL)

        # 2. 执行登录
        login_page.login("test001", "123456")

        # 3. 验证登录成功
        assert login_page.is_login_success(), "登录失败，未跳转到员工管理页面"
        # 进一步验证页面标题
        assert page.locator("h1").text_content() == "👥 员工信息管理"

    def test_login_wrong_password(self, page: Page):
        """
        反向用例：错误的密码
        """
        login_page = LoginPage(page)
        login_page.navigate(BASE_URL)

        login_page.login("test001", "wrong_password")

        # 验证未跳转
        assert not login_page.is_login_success(), "错误密码居然登录成功了？"
        # 验证错误信息显示
        assert login_page.is_error_displayed(), "未显示错误提示信息"
        error_msg = login_page.get_error_message()
        assert "用户名或密码错误" in error_msg or "401" in error_msg, f"错误信息不匹配: {error_msg}"

    def test_login_empty_username(self, page: Page):
        """
        反向用例：用户名为空
        """
        login_page = LoginPage(page)
        login_page.navigate(BASE_URL)

        login_page.login("", "123456")

        # 验证未跳转（Mock服务返回401）
        assert not login_page.is_login_success()
        # 错误信息可能为"用户名或密码错误"（Mock服务的行为）
        error_msg = login_page.get_error_message()
        assert error_msg != "", "应显示错误信息"

    def test_login_locked_account(self, page: Page):
        """
        反向用例：使用被锁定的账号登录
        """
        login_page = LoginPage(page)
        login_page.navigate(BASE_URL)

        login_page.login("locked_user", "any_password")

        # 验证未跳转
        assert not login_page.is_login_success()
        # 验证错误信息包含"锁定"字样
        error_msg = login_page.get_error_message()
        assert "锁定" in error_msg or "403" in error_msg, f"错误信息不包含锁定提示: {error_msg}"

    def test_login_disabled_account(self, page: Page):
        """
        反向用例：使用被禁用的账号登录
        """
        login_page = LoginPage(page)
        login_page.navigate(BASE_URL)

        login_page.login("disabled001", "any_password")

        assert not login_page.is_login_success()
        error_msg = login_page.get_error_message()
        assert error_msg != "", "应显示错误信息"


if __name__ == "__main__":
    # 直接运行此文件可进行简单调试
    pytest.main([__file__, "-v", "-s"])