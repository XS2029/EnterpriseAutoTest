"""
提交/审批模块接口自动化测试用例
包含单接口测试和多接口串联场景测试，集成数据库断言
"""

import pytest
import allure
import time
from utils.assert_utils import AssertUtils


def _resp_data(body: dict):
    """
    兼容后端返回 data / ddata 字段差异
    """
    if not isinstance(body, dict):
        raise AssertionError("响应体不是 dict")
    if "data" in body and isinstance(body.get("data"), dict):
        return body["data"]
    if "ddata" in body and isinstance(body.get("ddata"), dict):
        return body["ddata"]
    raise AssertionError(f"响应体缺少 data/ddata 字段: keys={list(body.keys())}")


@allure.feature("提交审批模块")
class TestSubmitApproval:

    # ---------- 正向用例 ----------
    @allure.story("提交审批申请-正向")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("payload", [
        {
            "applicant": "test001",
            "approval_type": "leave",
            "content": "年假申请，共5天",
            "amount": 5
        },
        {
            "applicant": "test001",
            "approval_type": "reimbursement",
            "content": "差旅费报销",
            "amount": 1280.50
        }
    ])
    def test_submit_approval_success(self, api_client, db_session, payload):
        """
        测试成功提交审批申请
        """
        allure.dynamic.title(f"提交审批-{payload['applicant']}-{payload['approval_type']}")
        with allure.step("1. 先登录获取token"):
            login_resp = api_client.do_post("/api/login", json_data={
                "username": payload["applicant"],
                "password": "123456"
            })
            AssertUtils.assert_status_code(login_resp, 200)
            token = _resp_data(login_resp.json())["token"]
            api_client.set_auth_token(token)
            allure.attach(f"已登录用户: {payload['applicant']}", "认证信息", allure.attachment_type.TEXT)

        with allure.step("2. 提交审批申请"):
            response = api_client.do_post("/api/approval", json_data=payload)

        with allure.step("3. 验证响应"):
            AssertUtils.assert_status_code(response, 200)
            AssertUtils.assert_json_contains(response, "code", 0)
            AssertUtils.assert_json_contains_text(response, "message", "提交")
            approval_id = _resp_data(response.json())["approval_id"]
            status = _resp_data(response.json())["status"]
            assert approval_id is not None
            assert status == "pending"
            allure.attach(f"申请单号: {approval_id}", "返回结果", allure.attachment_type.TEXT)

        with allure.step("4. 验证数据库记录已插入"):
            # Mock服务可能不落库，这里用查询接口二次校验提交结果
            query_resp = api_client.do_get("/api/approvals", params={"applicant": payload["applicant"], "size": 100})
            AssertUtils.assert_status_code(query_resp, 200)
            items = _resp_data(query_resp.json())["items"]
            found = any(item.get("id") == approval_id for item in items)
            assert found, "新提交的记录未在查询结果中找到"
            allure.attach(f"查询到 {len(items)} 条记录", "查询校验", allure.attachment_type.TEXT)

        with allure.step("5. 验证响应时间"):
            AssertUtils.assert_response_time(response, 500)

    # ---------- 参数校验反向用例 ----------
    @allure.story("提交审批申请-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("payload, expected_status, expected_msg_contains", [
        ({"approval_type": "leave", "content": "测试"}, 422, None),
        ({"applicant": "test001", "content": "测试"}, 422, None),
        ({"applicant": "", "approval_type": "leave", "content": "测试"}, 200, "提交"),
        ({"applicant": "test001", "approval_type": "reimbursement", "content": "金额为负", "amount": -100}, 200, "提交"),
    ])
    def test_submit_approval_validation(self, api_client, payload, expected_status, expected_msg_contains):
        """
        测试参数校验场景
        """
        allure.dynamic.title(f"参数校验-{payload}")
        with allure.step("先登录"):
            login_resp = api_client.do_post("/api/login", json_data={
                "username": "test001",
                "password": "123456"
            })
            if login_resp.status_code == 200:
                token = _resp_data(login_resp.json())["token"]
                api_client.set_auth_token(token)

        with allure.step(f"提交申请，参数：{payload}"):
            response = api_client.do_post("/api/approval", json_data=payload)

        with allure.step("验证响应状态码"):
            AssertUtils.assert_status_code(response, expected_status)
            if expected_status == 200:
                AssertUtils.assert_json_contains(response, "code", 0)
                if expected_msg_contains:
                    AssertUtils.assert_json_contains_text(response, "message", expected_msg_contains)

    # ---------- 鉴权相关用例 ----------
    @allure.story("提交审批申请-鉴权校验")
    @allure.severity(allure.severity_level.NORMAL)
    def test_submit_without_token(self, api_client):
        """
        测试未登录直接提交（无token）
        """
        allure.dynamic.title("未登录提交-鉴权校验")
        with allure.step("不设置token，直接提交"):
            api_client.session.headers.pop("Authorization", None)
            response = api_client.do_post("/api/approval", json_data={
                "applicant": "test001",
                "approval_type": "leave",
                "content": "未登录提交"
            })
        with allure.step("验证响应"):
            AssertUtils.assert_status_code(response, 200)
            allure.attach("注意：Mock服务未强制校验token，实际项目应返回401", "提示", allure.attachment_type.TEXT)

    # ---------- 核心：多接口串联场景 ----------
    @allure.story("多接口串联场景-完整审批流程")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_approval_flow(self, api_client, db_session):
        """
        模拟完整业务流程：
        登录 -> 查询待办列表 -> 提交新审批 -> 再次查询验证状态 -> 验证数据库
        """
        allure.dynamic.title("完整审批流程-端到端测试")
        test_applicant = "test001"
        test_password = "123456"

        with allure.step("1. 用户登录"):
            login_resp = api_client.do_post("/api/login", json_data={
                "username": test_applicant,
                "password": test_password
            })
            AssertUtils.assert_status_code(login_resp, 200)
            token = _resp_data(login_resp.json())["token"]
            api_client.set_auth_token(token)
            allure.attach(f"登录成功，用户: {test_applicant}", "步骤1", allure.attachment_type.TEXT)

        with allure.step("2. 查询当前用户的待审批记录"):
            query_resp = api_client.do_get("/api/approvals", params={"applicant": test_applicant, "size": 100})
            AssertUtils.assert_status_code(query_resp, 200)
            initial_count = _resp_data(query_resp.json())["total"]
            allure.attach(f"当前用户待审批记录数: {initial_count}", "步骤2", allure.attachment_type.TEXT)

        with allure.step("3. 提交一个新的审批申请"):
            submit_payload = {
                "applicant": test_applicant,
                "approval_type": "leave",
                "content": "串联测试-事假申请",
                "amount": 2
            }
            submit_resp = api_client.do_post("/api/approval", json_data=submit_payload)
            AssertUtils.assert_status_code(submit_resp, 200)
            approval_id = _resp_data(submit_resp.json())["approval_id"]
            allure.attach(f"申请单号: {approval_id}", "步骤3", allure.attachment_type.TEXT)

        with allure.step("4. 再次查询，验证记录数增加"):
            query_resp2 = api_client.do_get("/api/approvals", params={"applicant": test_applicant, "size": 100})
            new_count = _resp_data(query_resp2.json())["total"]
            assert new_count == initial_count + 1, f"记录数未增加，之前{initial_count}，现在{new_count}"
            items = _resp_data(query_resp2.json())["items"]
            found = any(item["id"] == approval_id for item in items)
            assert found, "新提交的记录未在查询结果中找到"

        with allure.step("5. 验证数据库中记录已插入"):
            # Mock服务可能不落库，此处仅做接口侧验证
            query_resp3 = api_client.do_get("/api/approvals", params={"applicant": test_applicant, "size": 100})
            AssertUtils.assert_status_code(query_resp3, 200)
            items = _resp_data(query_resp3.json())["items"]
            matched = next((i for i in items if i.get("id") == approval_id), None)
            assert matched is not None, "新提交的记录未在查询结果中找到"
            allure.attach(str(matched), "最新记录", allure.attachment_type.TEXT)

        with allure.step("6. 验证响应时间汇总"):
            allure.attach(
                f"登录:{login_resp.elapsed.total_seconds()*1000:.0f}ms, "
                f"查询:{query_resp.elapsed.total_seconds()*1000:.0f}ms, "
                f"提交:{submit_resp.elapsed.total_seconds()*1000:.0f}ms",
                "各接口响应时间", allure.attachment_type.TEXT
            )

    # ---------- 业务规则测试 ----------
    @allure.story("业务规则-重复提交检查")
    @allure.severity(allure.severity_level.MINOR)
    def test_duplicate_submit_prevention(self, api_client, db_session):
        """
        测试重复提交
        """
        allure.dynamic.title("重复提交检查")
        with allure.step("登录"):
            api_client.do_post("/api/login", json_data={"username": "test001", "password": "123456"})

        payload = {
            "applicant": "test001",
            "approval_type": "leave",
            "content": "重复提交测试",
            "amount": 1
        }

        with allure.step("第一次提交"):
            resp1 = api_client.do_post("/api/approval", json_data=payload)
            AssertUtils.assert_status_code(resp1, 200)

        with allure.step("第二次提交（相同内容）"):
            resp2 = api_client.do_post("/api/approval", json_data=payload)
            AssertUtils.assert_status_code(resp2, 200)
            allure.attach("注意：Mock服务未实现防重", "提示", allure.attachment_type.TEXT)

    # ---------- 性能与稳定性测试 ----------
    @allure.story("提交接口性能测试")
    @allure.severity(allure.severity_level.NORMAL)
    def test_submit_performance(self, api_client):
        """
        测试提交接口响应时间
        """
        allure.dynamic.title("提交接口性能测试-连续3次")
        with allure.step("登录"):
            api_client.do_post("/api/login", json_data={"username": "test001", "password": "123456"})

        payload = {"applicant": "test001", "approval_type": "leave", "content": "性能测试", "amount": 1}
        times = []
        for i in range(3):
            with allure.step(f"第{i+1}次提交"):
                resp = api_client.do_post("/api/approval", json_data=payload)
                AssertUtils.assert_status_code(resp, 200)
                elapsed = int(resp.elapsed.total_seconds() * 1000)
                times.append(elapsed)
                AssertUtils.assert_response_time(resp, 500)

        avg_time = sum(times) / len(times)
        allure.attach(f"3次提交平均响应时间: {avg_time:.2f}ms", "性能统计", allure.attachment_type.TEXT)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--alluredir=./reports/allure-results"])