"""
查询页面对象 (Page Object) - 优化版
"""

from playwright.sync_api import Page
from page_objects.base_page import BasePage


class QueryPage(BasePage):
    """员工查询页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.keyword_input = page.get_by_placeholder("输入姓名或部门搜索")
        self.search_button = page.get_by_role("button", name="搜 索")
        self.reset_button = page.get_by_role("button", name="重 置")
        self.page_input = page.locator("#page")
        self.size_select = page.locator("#size")
        self.table_body = page.locator("#table-body")
        self.pagination_info = page.locator("#pagination-info")

    def navigate(self, base_url: str = "http://127.0.0.1:8000"):
        self.navigate_to(f"{base_url}/employee-page")

    def search(self, keyword: str = "", page_num: int = None, size: int = None):
        """
        执行搜索操作（带重试和等待）
        """
        if keyword:
            self.safe_fill(self.keyword_input, keyword)
        if page_num is not None:
            self.safe_fill(self.page_input, str(page_num))
        if size is not None:
            self.size_select.select_option(str(size))
        self.safe_click(self.search_button)
        self._wait_for_table_load()

    def _wait_for_table_load(self):
        """等待表格数据加载完成"""
        # 等待 loading 消失（如果有）
        try:
            self.page.locator("#loading").wait_for(state="hidden", timeout=3000)
        except:
            pass
        # 等待表格至少有一行数据
        self.page.wait_for_function(
            """() => {
                const tbody = document.querySelector('#table-body');
                return tbody && tbody.children.length > 0;
            }""",
            timeout=8000
        )

    def reset_search(self):
        self.safe_click(self.reset_button)
        self._wait_for_table_load()

    def get_search_result_count(self) -> int:
        rows = self.table_body.locator("tr").all()
        count = 0
        for row in rows:
            if "暂无数据" not in (row.text_content() or ""):
                count += 1
        return count

    def get_total_count_from_pagination(self) -> int:
        import re
        info = self.pagination_info.text_content() or ""
        match = re.search(r"共 (\d+) 条", info)
        return int(match.group(1)) if match else 0

    def get_table_headers(self) -> list:
        return self.page.locator("th").all_text_contents()

    def get_row_data(self, row_index: int) -> dict:
        rows = self.table_body.locator("tr").all()
        if row_index >= len(rows):
            return {}
        cells = rows[row_index].locator("td").all_text_contents()
        headers = self.get_table_headers()
        return dict(zip(headers, cells))

    def is_no_data_displayed(self) -> bool:
        return "暂无数据" in (self.table_body.text_content() or "")