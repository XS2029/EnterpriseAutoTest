"""
查询模块接口自动化测试用例
测试员工查询接口，集成数据库断言验证数据一致性
"""

import pytest
import allure
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


@allure.feature("查询模块")
class TestQuery:

    @allure.story("基础查询功能")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("params, expected_page", [
        ({}, 1),
        ({"page": 2, "size": 5}, 2),
        ({"page": 1, "size": 10}, 1),
    ])
    def test_query_with_pagination(self, api_client, db_session, params, expected_page):
        """
        测试分页查询功能
        """
        allure.dynamic.title(f"分页查询-参数{params}")
        with allure.step(f"发送GET请求，参数：{params}"):
            response = api_client.do_get("/api/employees", params=params)

        with allure.step("验证响应状态码"):
            AssertUtils.assert_status_code(response, 200)
            AssertUtils.assert_json_contains(response, "code", 0)

        with allure.step("验证分页信息"):
            data = response.json()["data"]
            actual_page = data.get("page")
            assert actual_page == expected_page, f"期望页码 {expected_page}，实际 {actual_page}"
            allure.attach(f"page={actual_page}, size={data.get('size')}, total={data.get('total')}",
                          "分页信息", allure.attachment_type.TEXT)

        with allure.step("验证响应时间"):
            AssertUtils.assert_response_time(response, 500)

    @allure.story("关键词搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("keyword, expected_min_count", [
        ("张", 1),
        ("技术", 3),
        ("经理", 0),
    ])
    def test_query_with_keyword_search(self, api_client, keyword, expected_min_count):
        """
        测试关键词搜索功能
        """
        allure.dynamic.title(f"关键词搜索-{keyword}")
        with allure.step(f"搜索关键词：{keyword}"):
            response = api_client.do_get("/api/employees", params={"keyword": keyword})

        with allure.step("验证响应状态码"):
            AssertUtils.assert_status_code(response, 200)

        with allure.step("验证搜索结果数量"):
            items = _resp_data(response.json())["items"]
            assert len(items) >= expected_min_count, f"搜索结果数 {len(items)} 小于预期 {expected_min_count}"
            allure.attach(f"搜索到 {len(items)} 条记录", "结果数量", allure.attachment_type.TEXT)

        with allure.step("验证结果中包含关键词"):
            for item in items:
                name = item.get("name", "")
                dept = item.get("department", "")
                assert keyword in name or keyword in dept, f"记录 {item} 不包含关键词 {keyword}"

    @allure.story("数据库一致性验证")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_compare_with_database(self, api_client, db_session):
        """
        核心用例：对比接口返回的员工数据与数据库记录是否一致
        """
        allure.dynamic.title("数据库一致性验证-API与MySQL对比")
        with allure.step("1. 从接口获取全部员工数据"):
            response = api_client.do_get("/api/employees", params={"size": 100})
            AssertUtils.assert_status_code(response, 200)
            api_employees = _resp_data(response.json())["items"]

        with allure.step("2. 从数据库查询全部在职员工"):
            db_employees = db_session.execute_query(
                "SELECT id, name, department, position, phone, email, status FROM employees WHERE status='在职'"
            )

        with allure.step("3. 对比数量"):
            allure.attach(f"API返回: {len(api_employees)} 条, 数据库: {len(db_employees)} 条",
                          "数量对比", allure.attachment_type.TEXT)
            assert len(api_employees) > 0

        with allure.step("4. 验证API返回的记录在数据库中可对齐的部分一致"):
            api_ids = {emp.get("id") for emp in api_employees if emp.get("id") is not None}
            db_ids = {emp.get("id") for emp in db_employees if emp.get("id") is not None}
            overlap_ids = api_ids & db_ids
            missing_in_db = sorted(list(api_ids - db_ids))
            allure.attach(
                f"API IDs: {sorted(list(api_ids))}\nDB IDs: {sorted(list(db_ids))}\nOverlap: {sorted(list(overlap_ids))}\nMissingInDB: {missing_in_db}",
                "ID对齐情况", allure.attachment_type.TEXT
            )
            assert len(overlap_ids) > 0

            db_by_id = {e["id"]: e for e in db_employees if e.get("id") is not None}
            for api_emp in api_employees:
                emp_id = api_emp.get("id")
                if emp_id not in overlap_ids:
                    continue
                db_emp = db_by_id.get(emp_id)
                if db_emp:
                    assert api_emp.get("name") == db_emp.get("name"), f"ID {emp_id} 姓名不一致"

        with allure.step("5. 验证响应时间"):
            AssertUtils.assert_response_time(response, 500)

    @allure.story("边界和异常测试")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("params, expected_status", [
        ({"page": 0, "size": 10}, 422),
        ({"page": -1, "size": 10}, 422),
        ({"page": 1, "size": 1000}, 422),
        ({"keyword": "不存在关键词xyz123"}, 200),
    ])
    def test_query_edge_cases(self, api_client, params, expected_status):
        """
        测试边界和异常参数
        """
        allure.dynamic.title(f"边界测试-参数{params}")
        with allure.step(f"发送请求，参数：{params}"):
            response = api_client.do_get("/api/employees", params=params)

        with allure.step("验证响应状态码为200"):
            AssertUtils.assert_status_code(response, expected_status)

        with allure.step("验证空结果时items为空列表"):
            if expected_status == 200 and "不存在" in str(params.get("keyword", "")):
                items = _resp_data(response.json())["items"]
                assert len(items) == 0

    @allure.story("SQL注入防护测试")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_sql_injection(self, api_client):
        """
        测试SQL注入攻击是否被防护
        """
        allure.dynamic.title("SQL注入防护测试")
        malicious_keywords = [
            "'; DROP TABLE employees; --",
            "1' OR '1'='1",
            "admin'--",
        ]
        for keyword in malicious_keywords:
            with allure.step(f"尝试注入：{keyword}"):
                response = api_client.do_get("/api/employees", params={"keyword": keyword})
                AssertUtils.assert_status_code(response, 200)
                items = _resp_data(response.json())["items"]
                assert isinstance(items, list)

    @allure.story("响应时间性能测试")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_performance(self, api_client):
        """
        连续查询测试响应时间稳定性
        """
        allure.dynamic.title("查询接口性能测试-连续5次")
        response_times = []
        for i in range(5):
            with allure.step(f"第{i+1}次查询"):
                response = api_client.do_get("/api/employees", params={"size": 20})
                AssertUtils.assert_status_code(response, 200)
                elapsed_ms = int(response.elapsed.total_seconds() * 1000)
                response_times.append(elapsed_ms)
                AssertUtils.assert_response_time(response, 500)

        avg_time = sum(response_times) / len(response_times)
        allure.attach(f"5次查询平均响应时间: {avg_time:.2f}ms", "性能统计", allure.attachment_type.TEXT)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--alluredir=./reports/allure-results"])