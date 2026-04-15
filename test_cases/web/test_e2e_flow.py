"""
端到端业务流程测试用例 (E2E)
串联多个页面对象，模拟真实用户操作流程
"""

import pytest
import allure
from playwright.sync_api import Page
from page_objects.login_page import LoginPage
from page_objects.query_page import QueryPage
from utils.request_utils import RequestClient
from utils.assert_utils import AssertUtils
from config.settings import MOCK_API_URL

BASE_URL = MOCK_API_URL

@allure.feature("端到端业务流程")
class TestE2EFlow:

    @allure.story("场景1：登录→查询员工→查看详情→退出")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_login_query_view_logout(self, page: Page):
        """
        场景1完整流程：
        1. 用户登录
        2. 搜索特定员工
        3. 查看员工详情（通过点击行或API获取）
        4. 退出系统
        """
        with allure.step("1. 用户登录系统"):
            login_page = LoginPage(page)
            login_page.navigate(BASE_URL)
            login_page.login("test001", "123456")
            assert login_page.is_login_success(), "登录失败"
            allure.attach(page.screenshot(), "登录成功", allure.attachment_type.PNG)

        with allure.step("2. 搜索员工'张三'"):
            query_page = QueryPage(page)
            query_page.search(keyword="张三")
            count = query_page.get_search_result_count()
            assert count > 0, "未搜索到张三"
            allure.attach(f"搜索结果共 {count} 条", "搜索结果", allure.attachment_type.TEXT)

        with allure.step("3. 查看员工详情（模拟点击查看）"):
            # 由于Mock服务没有详情页，我们通过获取行数据来模拟
            row_data = query_page.get_row_data(0)
            assert row_data["姓名"] == "张三"
            allure.attach(str(row_data), "员工详情", allure.attachment_type.TEXT)
            # 实际项目中这里会是 page.click("查看详情") 并等待新页面

        with allure.step("4. 退出系统（模拟）"):
            # 实际退出可能点击"退出"按钮，这里我们直接关闭浏览器或导航回登录页
            page.goto(f"{BASE_URL}/login-page")
            assert "login" in page.url
            allure.attach("已返回登录页", "退出成功", allure.attachment_type.TEXT)

    @allure.story("场景2：登录→提交请假审批→查询审批记录→验证状态")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_submit_approval_and_verify(self, page: Page):
        """
        场景2完整流程：
        1. 用户登录
        2. 提交一个请假审批（通过API，因无UI表单）
        3. 查询审批记录（通过API查询并验证）
        4. 验证状态
        """
        # 步骤1：UI登录
        with allure.step("1. 用户登录系统"):
            login_page = LoginPage(page)
            login_page.navigate(BASE_URL)
            login_page.login("test001", "123456")
            assert login_page.is_login_success()
            # 获取token用于后续API调用（可以从cookie或localStorage获取，这里简化用API登录）
            # 实际场景中token通常在前端存储，我们用API客户端重新登录获取token
            api_client = RequestClient(BASE_URL)
            login_resp = api_client.do_post("/api/login", json_data={
                "username": "test001",
                "password": "123456"
            })
            token = login_resp.json()["data"]["token"]
            api_client.set_auth_token(token)
            allure.attach("登录成功，Token已获取", "认证", allure.attachment_type.TEXT)

        # 步骤2：提交审批（API模拟）
        with allure.step("2. 提交请假审批申请"):
            approval_data = {
                "applicant": "test001",
                "approval_type": "leave",
                "content": "E2E测试-年假申请",
                "amount": 3
            }
            submit_resp = api_client.do_post("/api/approval", json_data=approval_data)
            AssertUtils.assert_status_code(submit_resp, 200)
            approval_id = submit_resp.json()["data"]["approval_id"]
            allure.attach(f"申请单号: {approval_id}", "提交结果", allure.attachment_type.TEXT)

        # 步骤3：查询审批记录并验证
        with allure.step("3. 查询审批记录并验证状态"):
            # 其他测试可能已创建多条记录，默认 size=10 可能看不到刚提交的最后一条
            query_resp = api_client.do_get("/api/approvals", params={"applicant": "test001", "size": 100})
            AssertUtils.assert_status_code(query_resp, 200)
            items = query_resp.json()["data"]["items"]
            # 找到刚提交的审批
            found = False
            for item in items:
                if item["id"] == approval_id:
                    found = True
                    assert item["status"] == "pending"
                    allure.attach(f"审批状态: {item['status']}", "验证通过", allure.attachment_type.TEXT)
                    break
            assert found, "未在审批列表中查询到新提交的申请"

        with allure.step("4. 退出登录"):
            page.goto(f"{BASE_URL}/login-page")
            allure.attach("已返回登录页", "退出", allure.attachment_type.TEXT)

    @allure.story("场景3：登录→查询→修改信息（模拟）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_login_query_modify(self, page: Page):
        """
        场景3：由于Mock服务无编辑功能，模拟修改信息的流程
        1. 登录
        2. 查询员工
        3. 模拟点击编辑按钮（通过API更新数据库演示）
        4. 验证修改结果
        """
        with allure.step("1. 用户登录"):
            login_page = LoginPage(page)
            login_page.navigate(BASE_URL)
            login_page.login("test001", "123456")
            assert login_page.is_login_success()

        with allure.step("2. 查询员工'李四'"):
            query_page = QueryPage(page)
            query_page.search(keyword="李四")
            row_data = query_page.get_row_data(0)
            assert row_data["姓名"] == "李四"
            original_dept = row_data["部门"]
            allure.attach(f"原始部门: {original_dept}", "修改前", allure.attachment_type.TEXT)

        with allure.step("3. 模拟修改员工部门信息（通过API）"):
            # 实际UI操作可能为：点击编辑→修改部门→保存
            # 这里调用 mock 服务提供的更新接口，确保 UI 刷新后能看到变化
            api_client = RequestClient(BASE_URL)
            login_resp = api_client.do_post("/api/login", json_data={
                "username": "test001",
                "password": "123456"
            })
            api_client.set_auth_token(login_resp.json()["data"]["token"])
            api_client.do_put("/api/employees", json_data={
                "name": "李四",
                "department": "产品部"
            })
            allure.attach("部门已通过mock接口更新为'产品部'", "修改完成", allure.attachment_type.TEXT)

        with allure.step("4. 刷新页面并验证修改结果"):
            page.reload()
            query_page.search(keyword="李四")
            new_row = query_page.get_row_data(0)
            assert new_row["部门"] == "产品部"
            allure.attach(f"新部门: {new_row['部门']}", "验证通过", allure.attachment_type.TEXT)

            # 恢复数据（清理）
            api_client.do_put("/api/employees", json_data={
                "name": "李四",
                "department": "市场部"
            })


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--alluredir=./reports/allure-results"])