import re
from playwright.sync_api import Page, expect
from config.settings import MOCK_API_URL

def test_login_optimized(page: Page):
    # 1. 导航到登录页
    page.goto(f"{MOCK_API_URL}/login-page")

    # 2. 填写登录信息 - 优化点：使用更健壮的定位方式
    page.get_by_placeholder("用户名").fill("test001")  # Playwright推荐的语义化API
    page.get_by_placeholder("密码").fill("123456")

    # 3. 点击登录按钮 - 优化点：使用角色定位，更符合HTML语义
    page.get_by_role("button", name="登 录").click()

    # 4. 验证登录成功
    expect(page).to_have_url(re.compile(r".*employee-page"))
    expect(page.locator("h1")).to_contain_text("员工信息管理")

    # 5. 简单的查询操作
    page.get_by_placeholder("输入姓名或部门搜索").fill("技术")
    page.get_by_role("button", name="搜 索").click()

    # 6. 验证搜索结果
    expect(page.locator("#table-body")).to_contain_text("技术部")

    # 7. 等待2秒以便观察
    page.wait_for_timeout(2000)


if __name__ == "__main__":
    import sys
    import pytest

    raise SystemExit(pytest.main([__file__, "-s", "-v"]))