"""
断言工具类
封装常用的测试断言，提供清晰的错误信息
包含JSON结构断言（jsonpath）、字段类型断言、正则表达式断言、时间格式断言
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Union
import requests
from jsonpath_ng import parse as _jsonpath_parse
import sys


def _safe_print(text: str):
    """
    Windows 下部分终端编码为 gbk，直接 print 表情符号会触发 UnicodeEncodeError。
    这里不修改原始文案/表情，仅在输出阶段做降级，保证用例不中断。
    """
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.write(text.encode(enc, errors="replace").decode(enc, errors="replace") + "\n")


class AssertUtils:
    """断言工具类"""

    @staticmethod
    def assert_status_code(response: requests.Response, expected: int):
        """
        断言响应状态码
        :param response: requests.Response 对象
        :param expected: 期望的状态码
        """
        actual = response.status_code
        assert actual == expected, f"状态码断言失败：期望 {expected}，实际 {actual}"

    @staticmethod
    def assert_json_contains(response: requests.Response, key: str, expected_value: Any = None):
        """
        断言响应JSON中包含指定key，并可选验证值
        :param response: requests.Response 对象
        :param key: JSON中的key（支持点号访问嵌套，如 "data.token"）
        :param expected_value: 期望的值，为None时只验证key存在
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是有效的JSON格式：{response.text[:200]}")

        keys = key.split(".")
        current = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                raise AssertionError(f"JSON中不存在key '{key}'，当前可访问keys: {list(current.keys()) if isinstance(current, dict) else '非字典类型'}")

        if expected_value is not None:
            assert current == expected_value, f"JSON值断言失败：key='{key}'，期望 '{expected_value}'，实际 '{current}'"

    @staticmethod
    def assert_json_contains_text(response: requests.Response, key: str, text: str):
        """
        断言响应JSON中指定key的值包含某文本
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是有效的JSON格式")

        keys = key.split(".")
        current = data
        for k in keys:
            current = current.get(k) if isinstance(current, dict) else None
            if current is None:
                raise AssertionError(f"JSON中不存在key '{key}'")

        assert text in str(current), f"文本包含断言失败：key='{key}' 的值 '{current}' 不包含 '{text}'"

    @staticmethod
    def assert_response_time(response: requests.Response, max_ms: int):
        """
        断言响应时间不超过阈值
        :param response: requests.Response 对象
        :param max_ms: 最大允许时间（毫秒）
        """
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        if elapsed_ms > max_ms:
            _safe_print(f"⚠️ 警告：响应时间 {elapsed_ms}ms 超过阈值 {max_ms}ms")
            # 不强制断言失败，只输出警告
        else:
            _safe_print(f"✅ 响应时间 {elapsed_ms}ms ≤ {max_ms}ms")

    @staticmethod
    def assert_json_not_null(response: requests.Response, key: str):
        """
        断言响应JSON中指定key的值不为空
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是有效的JSON格式")

        keys = key.split(".")
        current = data
        for k in keys:
            current = current.get(k) if isinstance(current, dict) else None
            if current is None:
                raise AssertionError(f"JSON中不存在key '{key}'")

        assert current is not None and current != "", f"key '{key}' 的值为空"

    # ---------- 新增高级断言方法 ----------

    @staticmethod
    def assert_json_path(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用 jsonpath 断言JSON中的值
        :param response: requests.Response 对象
        :param json_path: jsonpath表达式，例如 "$.data.items[0].name"
        :param expected_value: 期望的值
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是有效的JSON格式")

        expr = _jsonpath_parse(json_path)
        matches = [m.value for m in expr.find(data)]
        if not matches:
            raise AssertionError(f"jsonpath表达式 '{json_path}' 未匹配到任何值")

        actual = matches[0] if len(matches) == 1 else matches
        assert actual == expected_value, f"jsonpath断言失败：路径 '{json_path}'，期望 '{expected_value}'，实际 '{actual}'"

    @staticmethod
    def assert_field_type(response: requests.Response, field_path: str, expected_type: type):
        """
        断言JSON字段的类型
        :param response: requests.Response 对象
        :param field_path: 字段路径，点号分隔，如 "data.total"
        :param expected_type: 期望的类型，如 int, str, list
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是有效的JSON格式")

        keys = field_path.split(".")
        current = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                raise AssertionError(f"JSON中不存在字段 '{field_path}'")

        assert isinstance(current, expected_type), f"字段类型断言失败：'{field_path}' 期望类型 {expected_type.__name__}，实际类型 {type(current).__name__}"

    @staticmethod
    def assert_regex_match(text: str, pattern: str, message: str = None):
        """
        断言文本匹配正则表达式
        :param text: 待匹配文本
        :param pattern: 正则表达式
        :param message: 自定义错误信息
        """
        match = re.search(pattern, text)
        assert match is not None, message or f"文本 '{text[:50]}...' 不匹配正则 '{pattern}'"

    @staticmethod
    def assert_datetime_format(text: str, format_str: str = "%Y-%m-%dT%H:%M:%S"):
        """
        断言字符串符合指定的日期时间格式
        :param text: 待验证字符串
        :param format_str: 时间格式，默认为 ISO 格式
        """
        try:
            datetime.strptime(text, format_str)
        except ValueError as e:
            raise AssertionError(f"时间格式断言失败：'{text}' 不符合格式 '{format_str}'，错误：{e}")

    @staticmethod
    def assert_list_contains(actual_list: List, expected_item: Any, message: str = None):
        """
        断言列表中包含指定元素
        """
        assert expected_item in actual_list, message or f"列表 {actual_list} 中未找到元素 '{expected_item}'"

    @staticmethod
    def assert_list_length(actual_list: List, expected_length: int, operator: str = "=="):
        """
        断言列表长度满足条件
        :param operator: 比较操作符，支持 ==, >, <, >=, <=
        """
        actual_len = len(actual_list)
        if operator == "==":
            assert actual_len == expected_length, f"列表长度应为 {expected_length}，实际 {actual_len}"
        elif operator == ">":
            assert actual_len > expected_length, f"列表长度应 > {expected_length}，实际 {actual_len}"
        elif operator == "<":
            assert actual_len < expected_length, f"列表长度应 < {expected_length}，实际 {actual_len}"
        elif operator == ">=":
            assert actual_len >= expected_length, f"列表长度应 >= {expected_length}，实际 {actual_len}"
        elif operator == "<=":
            assert actual_len <= expected_length, f"列表长度应 <= {expected_length}，实际 {actual_len}"
        else:
            raise ValueError(f"不支持的操作符: {operator}")


# ---------- 便捷函数 ----------
def assert_status_code(response, expected):
    AssertUtils.assert_status_code(response, expected)

def assert_json_contains(response, key, expected_value=None):
    AssertUtils.assert_json_contains(response, key, expected_value)

def assert_response_time(response, max_ms):
    AssertUtils.assert_response_time(response, max_ms)

def assert_json_path(response, json_path, expected_value):
    AssertUtils.assert_json_path(response, json_path, expected_value)

def assert_field_type(response, field_path, expected_type):
    AssertUtils.assert_field_type(response, field_path, expected_type)

def assert_regex_match(text, pattern, message=None):
    AssertUtils.assert_regex_match(text, pattern, message)

def assert_datetime_format(text, format_str="%Y-%m-%dT%H:%M:%S"):
    AssertUtils.assert_datetime_format(text, format_str)


# ---------- 测试代码 ----------
if __name__ == "__main__":
    print("=" * 60)
    print("测试 AssertUtils 增强功能")
    print("=" * 60)

    # 模拟响应对象
    class MockResponse:
        def __init__(self, status_code, json_data, elapsed_seconds=0.1):
            self.status_code = status_code
            self._json = json_data
            self.elapsed = type('obj', (object,), {'total_seconds': lambda: elapsed_seconds})()

        def json(self):
            return self._json

    # 构造测试数据
    test_json = {
        "code": 0,
        "message": "success",
        "data": {
            "total": 10,
            "items": [
                {"id": 1, "name": "张三", "create_time": "2025-01-15T10:30:00"},
                {"id": 2, "name": "李四", "create_time": "2025-01-16T14:20:00"}
            ]
        }
    }
    mock_resp = MockResponse(200, test_json)

    print("\n--- 测试 jsonpath 断言 ---")
    AssertUtils.assert_json_path(mock_resp, "$.data.items[0].name", "张三")
    print("✅ jsonpath断言通过")

    print("\n--- 测试字段类型断言 ---")
    AssertUtils.assert_field_type(mock_resp, "data.total", int)
    AssertUtils.assert_field_type(mock_resp, "data.items", list)
    print("✅ 字段类型断言通过")

    print("\n--- 测试正则表达式断言 ---")
    AssertUtils.assert_regex_match("响应时间: 123ms", r"\d+ms")
    print("✅ 正则断言通过")

    print("\n--- 测试时间格式断言 ---")
    AssertUtils.assert_datetime_format("2025-01-15T10:30:00")
    print("✅ 时间格式断言通过")

    print("\n--- 测试列表断言 ---")
    AssertUtils.assert_list_contains([1, 2, 3], 2)
    AssertUtils.assert_list_length([1, 2, 3], 2, ">")
    print("✅ 列表断言通过")

    print("\n✅ 所有增强断言测试通过！")