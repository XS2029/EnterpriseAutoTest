"""
Demo 测试用例（含日志与异常捕获演示）
用于验证 Pytest 框架、fixture、增强断言和日志系统
"""

import pytest
import allure
from utils.assert_utils import AssertUtils
from utils.log_utils import logger, LogContext
from config.settings import MOCK_API_URL


class TestDemo:
    """演示测试类"""

    @allure.story("框架基础验证")
    def test_base_url_fixture(self, base_url):
        """测试 base_url fixture"""
        logger.info(f"测试 base_url fixture，值为: {base_url}")
        assert base_url == MOCK_API_URL
        assert base_url.startswith("http")

    @allure.story("数据库连接验证")
    def test_db_connection(self, db_session):
        """测试数据库连接 fixture"""
        with LogContext(test_case="test_db_connection"):
            logger.info("开始测试数据库连接")
            result = db_session.execute_query("SELECT 1 as test")
            assert len(result) == 1
            assert result[0]["test"] == 1
            logger.success("数据库连接正常")

    @allure.story("API客户端验证")
    def test_api_client(self, api_client):
        """测试 API 客户端 fixture"""
        assert api_client is not None
        assert api_client.base_url == MOCK_API_URL
        logger.info(f"API客户端创建成功，base_url={api_client.base_url}")

    @allure.story("YAML读取器验证")
    def test_yaml_reader(self, yaml_reader):
        """测试 YAML 读取器 fixture"""
        try:
            data = yaml_reader.read_yaml("login_data.yaml")
            assert len(data) > 0
            logger.info(f"YAML读取成功，共有 {len(data)} 条登录用例数据")
        except Exception as e:
            logger.exception("YAML读取失败")
            raise

    @allure.story("测试数据获取验证")
    def test_get_test_data_fixture(self, get_test_data):
        """测试 get_test_data fixture"""
        case = get_test_data("login_data.yaml", "登录成功-正常用户名密码")
        assert case is not None
        assert case["casename"] == "登录成功-正常用户名密码"
        assert case["request"]["method"] == "POST"
        logger.info(f"获取测试数据成功: {case['casename']}")

    # ---------- 新增：高级断言演示 ----------
    @allure.story("高级断言演示")
    def test_advanced_assertions(self, api_client):
        """
        演示 jsonpath、字段类型、正则、时间格式等高级断言
        需要 Mock 服务运行
        """
        with LogContext(test_case="test_advanced_assertions"):
            logger.info("发送查询请求以测试高级断言")
            response = api_client.do_get("/api/employees", params={"size": 5})
            
            # jsonpath 断言
            AssertUtils.assert_json_path(response, "$.code", 0)
            logger.debug("jsonpath断言通过：$.code == 0")
            
            # 字段类型断言
            AssertUtils.assert_field_type(response, "data.total", int)
            AssertUtils.assert_field_type(response, "data.items", list)
            logger.debug("字段类型断言通过")
            
            # 正则断言（验证message）
            message = response.json().get("message", "")
            AssertUtils.assert_regex_match(message, r"success|成功")
            logger.debug("正则断言通过")
            
            logger.success("高级断言演示完成")

    # ---------- 故意失败的测试用例（用于验证日志和异常捕获） ----------
    @allure.story("异常捕获与日志验证")
    @pytest.mark.xfail(reason="这是一个故意写错断言的测试用例，用于验证日志和异常捕获", strict=False)
    def test_intentional_failure_for_logging(self, api_client):
        """
        这是一个故意写错断言的测试用例，用于验证：
        1. try-except 异常捕获
        2. 详细错误日志记录
        3. 失败时信息完整性
        """
        with LogContext(test_case="intentional_failure", expected_fail=True):
            logger.info("开始执行故意失败的测试用例")
            
            response = api_client.do_get("/api/employees")
            
            try:
                logger.debug("尝试一个必定失败的断言：期望状态码为 999")
                # 这行会抛出 AssertionError
                AssertUtils.assert_status_code(response, 999)
            except AssertionError as e:
                # 捕获异常，记录详细日志，然后重新抛出以便 pytest 标记为失败
                logger.error(f"断言失败（符合预期）: {e}")
                logger.exception("异常堆栈信息：")
                # 附加响应信息到日志
                logger.debug(f"实际响应状态码: {response.status_code}")
                logger.debug(f"响应体预览: {response.text[:200]}")
                # 重新抛出，让 pytest 知道这个测试失败了
                raise

            # 正常情况下不会执行到这里
            logger.warning("这行不应该被执行")
            assert False, "测试流程异常：应该已经抛出异常"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])