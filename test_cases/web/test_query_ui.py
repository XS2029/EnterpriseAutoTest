"""
查询页面 UI 自动化测试用例
基于 Page Object 模式
"""

import pytest
from playwright.sync_api import Page
from page_objects.query_page import QueryPage


class TestQueryUI:
    """查询页面测试类"""

    def test_search_by_keyword(self, authenticated_page: Page):
        """
        测试关键词搜索功能
        """
        query_page = QueryPage(authenticated_page)

        # 搜索"技术"
        query_page.search(keyword="技术")
        count = query_page.get_search_result_count()
        assert count > 0, "搜索结果应有数据"
        # 验证结果中包含"技术"（至少第一行包含）
        row_data = query_page.get_row_data(0)
        assert "技术" in row_data.get("部门", "") or "技术" in row_data.get("姓名", "")

    def test_search_no_result(self, authenticated_page: Page):
        """
        测试无结果搜索
        """
        query_page = QueryPage(authenticated_page)

        query_page.search(keyword="不存在的关键词xyz123")
        assert query_page.is_no_data_displayed(), "应显示暂无数据"
        assert query_page.get_search_result_count() == 0

    def test_pagination(self, authenticated_page: Page):
        """
        测试分页功能
        """
        query_page = QueryPage(authenticated_page)

        # 设置每页2条
        query_page.search(size=2)
        total = query_page.get_total_count_from_pagination()
        rows = query_page.get_search_result_count()
        # 每页应不超过2条（除非总数少于2）
        assert rows <= 2, f"每页应最多2条，实际{rows}条"
        # 如果总数大于2，应显示分页信息
        if total > 2:
            assert "第 1/" in query_page.pagination_info.text_content()

    def test_reset_search(self, authenticated_page: Page):
        """
        测试重置搜索功能
        """
        query_page = QueryPage(authenticated_page)

        # 先搜索一个关键词
        query_page.search(keyword="技术")
        count_after_search = query_page.get_search_result_count()
        # 点击重置
        query_page.reset_search()
        count_after_reset = query_page.get_search_result_count()
        # 重置后结果应变化（可能更多）
        # 至少验证重置后表格有数据
        assert count_after_reset > 0

    def test_table_data_display(self, authenticated_page: Page):
        """
        测试表格数据正常显示
        """
        query_page = QueryPage(authenticated_page)

        headers = query_page.get_table_headers()
        expected_headers = ["ID", "姓名", "部门", "职位", "电话", "邮箱", "状态"]
        for h in expected_headers:
            assert h in headers, f"表头应包含{h}"

        # 获取第一行数据
        row_data = query_page.get_row_data(0)
        assert row_data.get("ID") is not None
        assert row_data.get("姓名") is not None

    def test_switch_page_by_input(self, authenticated_page: Page):
        """
        测试通过页码输入框跳转
        """
        query_page = QueryPage(authenticated_page)

        total = query_page.get_total_count_from_pagination()
        if total <= 5:
            pytest.skip("总数据量不足以测试翻页")

        # 跳转到第2页
        query_page.search(page_num=2)
        # 验证页码变为2（从分页信息中）
        info_text = query_page.pagination_info.text_content()
        assert "第 2/" in info_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])