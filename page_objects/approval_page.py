"""
审批页面对象 (Page Object)
封装审批申请页面的元素定位和业务操作
注意：Mock服务目前无独立审批页面，此类作为扩展预留
"""

from playwright.sync_api import Page
from page_objects.base_page import BasePage


class ApprovalPage(BasePage):
    """审批申请页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 假设的元素定位器（实际需根据页面结构调整）
        self.applicant_input = page.locator("#applicant")
        self.type_select = page.locator("#approval_type")
        self.content_input = page.locator("#content")
        self.amount_input = page.locator("#amount")
        self.submit_button = page.get_by_role("button", name="提 交")
        self.success_message = page.locator(".success-message")

    def navigate(self, base_url: str = "http://127.0.0.1:8000"):
        """导航到审批申请页面（Mock服务暂无此页面）"""
        self.navigate_to(f"{base_url}/approval-page")

    def fill_form(self, data: dict):
        """
        填写审批表单
        :param data: 包含 applicant, approval_type, content, amount 等字段
        """
        if "applicant" in data:
            self.applicant_input.fill(data["applicant"])
        if "approval_type" in data:
            self.type_select.select_option(data["approval_type"])
        if "content" in data:
            self.content_input.fill(data["content"])
        if "amount" in data:
            self.amount_input.fill(str(data["amount"]))

    def submit(self):
        """提交审批申请"""
        self.submit_button.click()

    def get_success_message(self) -> str:
        """获取成功提示信息"""
        try:
            self.success_message.wait_for(state="visible", timeout=3000)
            return self.success_message.text_content() or ""
        except:
            return ""

    def is_submit_success(self) -> bool:
        """判断是否提交成功"""
        return self.get_success_message() != ""