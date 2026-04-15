"""
Pytest 全局配置（fixtures / hooks）

说明：
- 项目最初将这些 fixtures 放在了 `utils/assert_utils.py` 中，pytest 默认不会去那里发现它们。
- 这里通过导入的方式暴露为全局 fixtures，确保用例可以直接使用 `base_url`、`api_client` 等。
"""

import pytest
import sys
import os
import re
import datetime
import subprocess
import time
import json
import urllib.request
import urllib.error

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_mock_server_proc: subprocess.Popen | None = None


def _openapi_has_put_employees(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/openapi.json", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        paths = data.get("paths") or {}
        put = ((paths.get("/api/employees") or {}).get("put")) is not None
        return bool(put)
    except Exception:
        return False


def _wait_http_ok(url: str, timeout_s: float = 10.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def _ensure_mock_base_url() -> str:
    """
    确保 mock 服务可用，并且具备 /api/employees 的 PUT（用于 E2E 修改场景）。
    - 若 8000 已是新版本：直接使用
    - 否则在 8001 拉起当前代码版本，并通过环境变量覆盖 MOCK_API_URL
    """
    global _mock_server_proc
    primary = "http://127.0.0.1:8000"
    if _openapi_has_put_employees(primary):
        return primary

    # 8000 不满足（可能未启动或是旧服务），用 8001 启动当前版本
    fallback = "http://127.0.0.1:8001"
    if _openapi_has_put_employees(fallback):
        return fallback

    # 启动 uvicorn（不占用当前 pytest 进程）
    env = os.environ.copy()
    env["PYTHONUTF8"] = env.get("PYTHONUTF8", "1")
    _mock_server_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mock_server.mock_api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--log-level",
            "warning",
        ],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_http_ok(f"{fallback}/openapi.json", timeout_s=12):
        return primary  # 兜底：保持原样，不阻塞测试启动
    return fallback


# 在导入 settings 前确定 MOCK_API_URL（让全项目统一使用同一 base_url）
os.environ.setdefault("MOCK_API_URL", _ensure_mock_base_url())

from config.settings import DB_CONFIG, MOCK_API_URL, TEST_CONFIG
from utils.db_utils import MySQLHelper
from utils.request_utils import RequestClient
from utils.yaml_reader import YAMLReader


def pytest_addoption(parser):
    """
    UI 多浏览器支持：
    - --browser all            （默认：chromium, firefox, webkit）
    - --browser chromium
    - --browser chromium,firefox
    - --headed                （强制有界面；默认有界面，传 --headed 也可）
    - --headless              （无界面）
    """
    parser.addoption(
        "--browser",
        action="store",
        default="all",
        help="Playwright browser: all|chromium|firefox|webkit 或逗号分隔列表",
    )
    parser.addoption("--headed", action="store_true", default=False, help="Run browser headed")
    parser.addoption("--headless", action="store_true", default=False, help="Run browser headless")


def _resolve_browsers(config) -> list[str]:
    raw = (config.getoption("--browser") or "all").strip().lower()
    if raw in ("all", "*"):
        return ["chromium", "firefox", "webkit"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    allowed = {"chromium", "firefox", "webkit"}
    browsers = [p for p in parts if p in allowed]
    return browsers or ["chromium"]


def pytest_generate_tests(metafunc):
    # 只有依赖 browser_name fixture 的测试才会被参数化为多浏览器
    if "browser_name" in metafunc.fixturenames:
        browsers = _resolve_browsers(metafunc.config)
        metafunc.parametrize("browser_name", browsers, scope="function")


@pytest.fixture(scope="session")
def base_url():
    """Mock服务的基础URL"""
    return MOCK_API_URL


@pytest.fixture(scope="session")
def db_helper():
    """数据库操作助手（会话级别，整个测试会话只创建一次连接）"""
    helper = MySQLHelper(DB_CONFIG)
    helper.get_connection()
    yield helper
    helper.close()


@pytest.fixture(scope="function")
def db_session(db_helper):
    """
    数据库会话（函数级别，每个测试用例执行前后可以回滚）
    注意：由于 MySQL 不支持事务回滚已提交的变更，这里仅提供清理建议
    """
    yield db_helper


@pytest.fixture(scope="function")
def api_client(base_url):
    """API请求客户端（每个测试用例独立的会话）"""
    client = RequestClient(
        base_url=base_url,
        timeout=TEST_CONFIG.get("api_timeout", 10)
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def yaml_reader():
    """YAML数据读取器"""
    return YAMLReader()


@pytest.fixture
def get_test_data(yaml_reader):
    """
    获取测试数据的便捷函数
    使用方式：data = get_test_data('login_data.yaml', '登录成功-正常用户名密码')
    """
    def _get_data(file_name: str, case_name: str):
        return yaml_reader.get_test_data(file_name, case_name)
    return _get_data


@pytest.fixture
def get_all_test_data(yaml_reader):
    """
    获取文件中所有测试数据的便捷函数（用于参数化）
    """
    def _get_all(file_name: str):
        return yaml_reader.read_yaml(file_name)
    return _get_all


# ---------- UI 多浏览器 fixtures（Playwright） ----------
@pytest.fixture
def browser_name(request) -> str:
    return request.param


@pytest.fixture(scope="session")
def playwright():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="function")
def browser(playwright, browser_name, request):
    # 默认 headed（更适合教学/演示）；传 --headless 可切换
    headless = bool(request.config.getoption("--headless"))
    if request.config.getoption("--headed"):
        headless = False

    slow_mo = int(os.getenv("PW_SLOW_MO", "0") or 0)
    browser_type = getattr(playwright, browser_name)
    b = browser_type.launch(headless=headless, slow_mo=slow_mo)
    yield b
    b.close()


@pytest.fixture(scope="function")
def context(browser):
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context):
    p = context.new_page()
    yield p


@pytest.fixture(scope="function")
def authenticated_page(page):
    """已登录的 Page（供所有 UI 用例复用）"""
    from page_objects.login_page import LoginPage

    login_page = LoginPage(page)
    login_page.navigate(MOCK_API_URL)
    login_page.login("test001", "123456")
    page.wait_for_url("**/employee-page")
    return page


# ---------- Pytest 钩子函数 ----------
def pytest_configure(config):
    """Pytest 启动时的配置"""
    # 添加自定义标记
    config.addinivalue_line("markers", "smoke: 冒烟测试用例")
    config.addinivalue_line("markers", "api: API接口测试")
    config.addinivalue_line("markers", "ui: UI自动化测试")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时，关闭我们启动的 mock 服务"""
    global _mock_server_proc
    if _mock_server_proc is not None:
        try:
            _mock_server_proc.terminate()
            _mock_server_proc.wait(timeout=5)
        except Exception:
            pass
        _mock_server_proc = None


def pytest_collection_modifyitems(items):
    """修改收集到的测试用例，为未标记的用例添加默认标记"""
    for item in items:
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "web" in item.nodeid or "ui" in item.nodeid:
            item.add_marker(pytest.mark.ui)


@pytest.fixture(autouse=True)
def log_test_info(request):
    """自动记录每个测试用例的开始和结束（便于调试）"""
    print(f"\n{'='*60}")
    print(f"开始执行测试: {request.node.name}")
    print(f"   文件位置: {request.fspath}")
    yield
    print(f"测试结束: {request.node.name}")
    print(f"{'='*60}\n")


def _safe_filename(name: str) -> str:
    name = re.sub(r"[\\/:\*\?\"<>\|\s]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "test"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    用例失败时自动截图，保存到 screenshots/ 目录。
    - Playwright: 需要能从 item.funcargs 或 item 上拿到 page
    - Selenium: 需要能从 item.funcargs 或 item 上拿到 driver
    """
    outcome = yield
    rep = outcome.get_result()

    # 仅在“执行阶段”失败时截图（setup/teardown 可按需改为也截图）
    if rep.when != "call" or not rep.failed:
        return

    project_root = os.path.dirname(os.path.abspath(__file__))
    screenshots_dir = os.path.join(project_root, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = _safe_filename(item.nodeid)
    file_path = os.path.join(screenshots_dir, f"{base}_{ts}.png")

    # 优先从 fixture 里拿
    page = None
    driver = None
    try:
        page = item.funcargs.get("page")
    except Exception:
        page = None
    try:
        driver = item.funcargs.get("driver")
    except Exception:
        driver = None

    # 兼容：fixture 名不是 page（例如 authenticated_page）
    if page is None:
        try:
            for _name, _obj in (item.funcargs or {}).items():
                # Playwright Page 有 screenshot(path=...) 方法（duck-typing，避免强依赖类型导入）
                if _obj is not None and callable(getattr(_obj, "screenshot", None)):
                    page = _obj
                    break
        except Exception:
            page = None

    # 兼容：有的项目会在 fixture 里把 page/driver 挂到 item 上
    if page is None:
        page = getattr(item, "page", None)
    if driver is None:
        driver = getattr(item, "driver", None)

    saved = False
    err = None

    # Playwright
    if page is not None:
        try:
            page.screenshot(path=file_path, full_page=True)
            saved = True
        except Exception as e:
            err = e

    # Selenium（若 Playwright 没拿到或保存失败）
    if not saved and driver is not None:
        try:
            driver.get_screenshot_as_file(file_path)
            saved = True
        except Exception as e:
            err = e

    if saved:
        print(f"[截图] 用例失败已保存: {file_path}")
    else:
        if err is not None:
            print(f"[截图] 用例失败但截图保存失败: {err}")
        else:
            print("[截图] 用例失败但未找到可截图对象（page/driver fixture 不存在）")

