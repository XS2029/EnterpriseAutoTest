"""
HTTP 请求封装工具类
基于 requests 库，提供统一的请求发送和响应处理
"""

import requests
import json
from typing import Optional, Dict, Any, Union
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


class RequestClient:
    """HTTP 请求客户端封装"""

    def __init__(self, base_url: str = "", timeout: int = 10):
        """
        初始化客户端
        :param base_url: 服务基础URL
        :param timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.timeout = timeout
        self.session = requests.Session()
        # 默认请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "EnterpriseAutoTest/1.0"
        })

    def _build_url(self, path: str) -> str:
        """构建完整URL"""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        path = path.lstrip("/")
        return f"{self.base_url}/{path}" if self.base_url else path

    def do_get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> requests.Response:
        """
        发送 GET 请求
        :param url: 请求路径
        :param params: URL查询参数
        :param headers: 额外请求头
        :return: Response对象
        """
        full_url = self._build_url(url)
        _safe_print(f"🌐 GET {full_url}")
        if params:
            _safe_print(f"   Params: {params}")
        response = self.session.get(
            full_url,
            params=params,
            headers=headers,
            timeout=self.timeout
        )
        self._log_response(response)
        return response

    def do_post(self, url: str, data: Any = None, json_data: Any = None, headers: Optional[Dict] = None) -> requests.Response:
        """
        发送 POST 请求
        :param url: 请求路径
        :param data: 表单数据
        :param json_data: JSON数据
        :param headers: 额外请求头
        :return: Response对象
        """
        full_url = self._build_url(url)
        _safe_print(f"🌐 POST {full_url}")
        if json_data:
            _safe_print(f"   JSON: {json.dumps(json_data, ensure_ascii=False)}")
        response = self.session.post(
            full_url,
            data=data,
            json=json_data,
            headers=headers,
            timeout=self.timeout
        )
        self._log_response(response)
        return response

    def do_put(self, url: str, data: Any = None, json_data: Any = None, headers: Optional[Dict] = None) -> requests.Response:
        """
        发送 PUT 请求
        """
        full_url = self._build_url(url)
        _safe_print(f"🌐 PUT {full_url}")
        response = self.session.put(
            full_url,
            data=data,
            json=json_data,
            headers=headers,
            timeout=self.timeout
        )
        self._log_response(response)
        return response

    def do_delete(self, url: str, headers: Optional[Dict] = None) -> requests.Response:
        """
        发送 DELETE 请求
        """
        full_url = self._build_url(url)
        _safe_print(f"🌐 DELETE {full_url}")
        response = self.session.delete(
            full_url,
            headers=headers,
            timeout=self.timeout
        )
        self._log_response(response)
        return response

    def _log_response(self, response: requests.Response):
        """记录响应信息"""
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        try:
            resp_body = response.json()
            body_preview = json.dumps(resp_body, ensure_ascii=False)[:200]
        except:
            body_preview = response.text[:200] if response.text else "(empty)"
        _safe_print(f"   ⏱️ {elapsed_ms}ms | Status: {response.status_code} | Body: {body_preview}")

    def set_header(self, key: str, value: str):
        """设置全局请求头"""
        self.session.headers.update({key: value})

    def set_auth_token(self, token: str, scheme: str = "Bearer"):
        """设置认证Token"""
        self.set_header("Authorization", f"{scheme} {token}")

    def close(self):
        """关闭会话"""
        self.session.close()


# ---------- 测试代码 ----------
if __name__ == "__main__":
    print("=" * 50)
    print("测试 RequestClient")
    print("=" * 50)

    client = RequestClient(base_url="https://httpbin.org")
    try:
        # 测试 GET
        print("\n--- 测试 GET ---")
        resp_get = client.do_get("/get", params={"foo": "bar"})
        assert resp_get.status_code == 200

        # 测试 POST
        print("\n--- 测试 POST ---")
        resp_post = client.do_post("/post", json_data={"name": "test", "value": 123})
        assert resp_post.status_code == 200

        print("\n✅ RequestClient 测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        client.close()