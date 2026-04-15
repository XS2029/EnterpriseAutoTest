"""
登录模块接口自动化测试用例
使用数据驱动方式，从 YAML 文件读取测试数据
"""

import pytest
import allure
from utils.assert_utils import AssertUtils


@allure.epic("接口自动化测试")
@allure.feature("登录模块")
class TestLogin:

    @allure.story("登录正向用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("case_data", [
        {"casename": "登录成功-正常用户名密码"},
        {"casename": "登录成功-管理员账号"}
    ])
    def test_login_success(self, api_client, get_test_data, case_data):
        """
        测试登录成功场景
        """
        casename = case_data["casename"]
        data = get_test_data("login_data.yaml", casename)
        assert data is not None, f"未找到用例数据: {casename}"

        allure.dynamic.title(casename)
        allure.dynamic.description(data.get("description", ""))
        allure.dynamic.tag("正向用例", "核心功能")

        with allure.step("发送登录请求"):
            request_info = data["request"]
            response = api_client.do_post(
                url=request_info["url"],
                json_data=request_info["json"]
            )

        with allure.step("验证响应状态码和业务码"):
            AssertUtils.assert_status_code(response, 200)
            AssertUtils.assert_json_contains(response, "code", 0)
            AssertUtils.assert_json_contains(response, "message", "登录成功")

        with allure.step("验证返回token"):
            token = response.json()["data"]["token"]
            assert token is not None and token != ""
            allure.attach(f"Token: {token[:20]}...", "Token信息", allure.attachment_type.TEXT)
            # 保存token到全局变量供后续接口使用
            api_client.set_auth_token(token)

        with allure.step("验证返回用户名和角色"):
            expected_username = request_info["json"]["username"]
            actual_username = response.json()["data"]["username"]
            assert actual_username == expected_username

    @allure.story("登录反向用例")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("case_data", [
        {"casename": "登录失败-错误密码"},
        {"casename": "登录失败-不存在的用户"},
        {"casename": "登录失败-用户名为空"},
        {"casename": "登录失败-密码为空"},
        {"casename": "登录失败-超长用户名"},
        {"casename": "登录失败-SQL注入尝试"}
    ])
    def test_login_fail_unauthorized(self, api_client, get_test_data, case_data):
        """
        测试登录失败场景（返回401）
        """
        casename = case_data["casename"]
        data = get_test_data("login_data.yaml", casename)
        assert data is not None, f"未找到用例数据: {casename}"

        allure.dynamic.title(casename)
        allure.dynamic.description(data.get("description", ""))
        allure.dynamic.tag("反向用例", "异常测试")

        with allure.step("发送登录请求"):
            request_info = data["request"]
            response = api_client.do_post(
                url=request_info["url"],
                json_data=request_info["json"]
            )

        with allure.step("验证响应状态码为401"):
            AssertUtils.assert_status_code(response, 401)
            AssertUtils.assert_json_contains(response, "code", 401)

        with allure.step("验证错误消息"):
            message = response.json().get("message", "")
            assert "用户名或密码错误" in message or "错误" in message

    @allure.story("登录状态相关用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("case_data", [
        {"casename": "登录失败-账号被锁定"},
        {"casename": "登录失败-账号被禁用"}
    ])
    def test_login_fail_forbidden(self, api_client, get_test_data, case_data):
        """
        测试账号锁定/禁用场景（返回403）
        """
        casename = case_data["casename"]
        data = get_test_data("login_data.yaml", casename)
        assert data is not None, f"未找到用例数据: {casename}"

        allure.dynamic.title(casename)
        allure.dynamic.description(data.get("description", ""))
        allure.dynamic.tag("状态相关", "异常测试")

        with allure.step("发送登录请求"):
            request_info = data["request"]
            response = api_client.do_post(
                url=request_info["url"],
                json_data=request_info["json"]
            )

        with allure.step("验证响应状态码为403"):
            AssertUtils.assert_status_code(response, 403)
            AssertUtils.assert_json_contains(response, "code", 403)

        with allure.step("验证错误消息"):
            message = response.json().get("message", "")
            assert "锁定" in message or "禁用" in message

    @allure.story("登录性能验证")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("登录接口响应时间测试")
    def test_login_response_time(self, api_client):
        """
        测试登录接口响应时间
        """
        allure.dynamic.tag("性能测试")
        with allure.step("发送正常登录请求"):
            response = api_client.do_post(
                url="/api/login",
                json_data={"username": "test001", "password": "123456"}
            )

        with allure.step("验证响应状态码"):
            AssertUtils.assert_status_code(response, 200)

        with allure.step("验证响应时间不超过500ms"):
            AssertUtils.assert_response_time(response, 500)
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)
            allure.attach(f"响应时间: {elapsed_ms}ms", "性能数据", allure.attachment_type.TEXT)

    @allure.story("Token有效性验证")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("登录后Token可用于后续请求")
    def test_login_token_validity(self, api_client):
        """
        验证获取的Token可以用于后续请求（通过调用一个需要鉴权的接口）
        """
        allure.dynamic.tag("集成测试")
        with allure.step("1. 先登录获取token"):
            login_resp = api_client.do_post(
                url="/api/login",
                json_data={"username": "test001", "password": "123456"}
            )
            token = login_resp.json()["data"]["token"]

        with allure.step("2. 使用token调用查询接口"):
            api_client.set_auth_token(token)
            query_resp = api_client.do_get("/api/employees", params={"page": 1, "size": 5})

        with allure.step("3. 验证查询成功"):
            AssertUtils.assert_status_code(query_resp, 200)
            AssertUtils.assert_json_contains(query_resp, "code", 0)
            allure.attach("Token携带成功，查询接口正常返回", "验证结果", allure.attachment_type.TEXT)


if __name__ == "__main__":
    # 调试运行
    pytest.main([__file__, "-v", "-s", "--alluredir=./reports/allure-results"])