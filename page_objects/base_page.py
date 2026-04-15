"""
Page Object 基类（增强版）
- 智能等待策略
- 自动重试机制
- 多浏览器兼容支持
"""

from playwright.sync_api import Page, expect, Locator, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Callable, Union
import time


class BasePage:
    """页面基类，所有页面对象继承此类"""

    def __init__(self, page: Page):
        self.page = page
        self.default_timeout = 15000  # 默认超时 15 秒
        self.retry_attempts = 2       # 默认重试次数

    def navigate_to(self, url: str, wait_until: str = "networkidle"):
        """
        导航到指定 URL，并等待页面加载完成
        :param url: 目标 URL
        :param wait_until: 等待状态，可选 "load", "domcontentloaded", "networkidle"
        """
        self.page.goto(url, wait_until=wait_until)
        # 额外等待网络空闲，确保动态内容加载完成
        self.page.wait_for_load_state("networkidle")

    def wait_for_element(self, selector: Union[str, Locator], timeout: Optional[int] = None, state: str = "visible") -> Locator:
        """
        智能等待元素出现并返回 Locator
        :param selector: 选择器（支持CSS、文本、角色等）
        :param timeout: 超时时间（毫秒）
        :param state: 等待状态 "attached", "detached", "visible", "hidden"
        :return: Locator 对象
        """
        timeout = timeout or self.default_timeout
        locator = selector if isinstance(selector, Locator) else self.page.locator(selector)
        locator.wait_for(state=state, timeout=timeout)
        return locator

    def wait_for_text(self, text: str, timeout: Optional[int] = None) -> Locator:
        """等待包含指定文本的元素出现"""
        timeout = timeout or self.default_timeout
        locator = self.page.get_by_text(text)
        locator.first.wait_for(state="visible", timeout=timeout)
        return locator

    def click_with_retry(self, selector: Union[str, Locator], retries: int = None):
        """
        带重试机制的点击操作
        :param selector: 元素选择器
        :param retries: 重试次数，默认使用实例配置
        """
        retries = retries or self.retry_attempts
        last_exception = None
        for attempt in range(retries + 1):
            try:
                locator = self.wait_for_element(selector, timeout=5000)
                locator.click()
                return
            except Exception as e:
                last_exception = e
                if attempt < retries:
                    print(f"⚠️ 点击失败（尝试 {attempt + 1}/{retries + 1}），等待后重试...")
                    time.sleep(1)
        raise last_exception or Exception(f"点击操作失败，已重试 {retries} 次")

    def fill_with_retry(self, selector: Union[str, Locator], value: str, retries: int = None):
        """
        带重试机制的输入操作
        """
        retries = retries or self.retry_attempts
        last_exception = None
        for attempt in range(retries + 1):
            try:
                locator = self.wait_for_element(selector, timeout=5000)
                locator.clear()
                locator.fill(value)
                return
            except Exception as e:
                last_exception = e
                if attempt < retries:
                    print(f"⚠️ 输入失败（尝试 {attempt + 1}/{retries + 1}），等待后重试...")
                    time.sleep(1)
        raise last_exception or Exception(f"输入操作失败，已重试 {retries} 次")

    def get_text(self, selector: Union[str, Locator]) -> str:
        """获取元素文本内容"""
        locator = self.wait_for_element(selector)
        return locator.text_content() or ""

    def is_visible(self, selector: Union[str, Locator], timeout: int = 2000) -> bool:
        """快速判断元素是否可见"""
        try:
            (selector if isinstance(selector, Locator) else self.page.locator(selector)).wait_for(state="visible", timeout=timeout)
            return True
        except:
            return False

    def wait_for_navigation(self, url_pattern: str = None, timeout: int = None):
        """
        等待页面导航完成
        :param url_pattern: URL 匹配模式，如 "**/employee-page"
        """
        timeout = timeout or self.default_timeout
        if url_pattern:
            self.page.wait_for_url(url_pattern, timeout=timeout)
        else:
            self.page.wait_for_load_state("networkidle", timeout=timeout)

    def safe_click(self, selector: Union[str, Locator]):
        """
        安全点击：先等待元素可点击，再点击
        """
        locator = self.wait_for_element(selector)
        locator.scroll_into_view_if_needed()  # 滚动到可见区域
        try:
            locator.click()
        except PlaywrightTimeoutError:
            # 个别浏览器/环境下可能出现“始终不稳定”的情况，最后兜底强制点击
            locator.click(force=True)

    def safe_fill(self, selector: Union[str, Locator], value: str):
        """
        安全输入：等待元素可编辑，清空后输入
        """
        locator = self.wait_for_element(selector)
        locator.scroll_into_view_if_needed()
        locator.clear()
        locator.fill(value)

    def get_current_url(self) -> str:
        return self.page.url

    def take_screenshot(self, name: str = "screenshot"):
        """截图并返回二进制数据"""
        return self.page.screenshot(full_page=True)