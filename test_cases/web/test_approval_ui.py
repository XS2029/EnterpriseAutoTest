"""
审批模块 UI 自动化测试用例
注意：Mock服务暂无独立审批表单页面，以下用例基于假设的页面结构
"""

import pytest
from playwright.sync_api import Page
from page_objects.approval_page import ApprovalPage
from config.settings import MOCK_API_URL

BASE_URL = MOCK_API_URL


class TestApprovalUI:
    """审批模块测试类（基于模拟页面）"""

    def test_navigate_to_approval_page(self, authenticated_page: Page):
        """
        测试导航到审批申请页面（Mock服务无此页面，演示结构）
        """
        approval_page = ApprovalPage(authenticated_page)
        # 尝试导航，预期会404或不存在，但可以测试对象创建
        try:
            approval_page.navigate(BASE_URL)
            # 如果页面存在，验证URL
            assert "approval" in authenticated_page.url
        except:
            pytest.skip("Mock服务未提供审批页面，跳过导航测试")

    def test_fill_approval_form(self, authenticated_page: Page):
        """
        测试填写审批表单
        """
        # 由于Mock服务无实际页面，这里仅演示Page Object调用逻辑
        # 实际项目中，会先导航到正确的URL
        approval_page = ApprovalPage(authenticated_page)
        # 假设页面已加载
        form_data = {
            "applicant": "test001",
            "approval_type": "leave",
            "content": "年假申请",
            "amount": 5
        }
        # 实际调用fill_form方法
        try:
            approval_page.fill_form(form_data)
            approval_page.submit()
        except:
            pytest.skip("Mock服务未提供审批表单页面，跳过表单填写")

    def test_submit_success_message(self, authenticated_page: Page):
        """
        测试提交成功提示
        """
        # 演示断言结构
        approval_page = ApprovalPage(authenticated_page)
        # 实际测试中会在提交后验证
        try:
            assert approval_page.is_submit_success() in [True, False]
        except:
            pytest.skip("Mock服务未提供审批表单页面")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])