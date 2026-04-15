"""
Mock API 服务 - 模拟企业管理系统后端接口
使用 FastAPI 框架，提供登录、员工查询、审批提交等接口
"""

import os
import yaml
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

# 创建 FastAPI 应用实例
app = FastAPI(
    title="企业管理系统 Mock API",
    description="用于自动化测试框架的模拟后端服务",
    version="1.0.0"
)

# 加载配置文件
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "mock_config.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# 内存数据存储（模拟数据库）
employees_data = CONFIG.get("employees", [])
approvals_data = CONFIG.get("approvals", {}).get("records", [])
next_approval_id = CONFIG.get("approvals", {}).get("next_id", 1001)
valid_users = CONFIG.get("login", {}).get("valid_users", {})
locked_users = CONFIG.get("login", {}).get("locked_users", [])
token_prefix = CONFIG.get("login", {}).get("token_prefix", "mock_token_")

# ---------- 请求/响应模型 ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None

class ApprovalRequest(BaseModel):
    applicant: str
    approval_type: str  # leave, reimbursement, etc.
    content: str
    amount: Optional[float] = None

class ApprovalResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class EmployeeUpdateRequest(BaseModel):
    """员工信息更新请求（仅用于 mock 测试演示）"""
    name: str
    department: Optional[str] = None

# ---------- 辅助函数 ----------
def generate_token(username: str) -> str:
    """生成模拟 Token"""
    return f"{token_prefix}{username}_{uuid.uuid4().hex[:8]}"

def paginate_items(items: List[Dict], page: int = 1, size: int = 10) -> Dict:
    """分页处理"""
    total = len(items)
    start = (page - 1) * size
    end = start + size
    paginated = items[start:end]
    return {
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
        "items": paginated
    }

# ---------- 接口定义 ----------

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 显示服务状态"""
    return """
    <html>
        <head><title>企业管理系统 Mock API</title></head>
        <body style="font-family: Arial; padding: 40px;">
            <h1>🏢 企业管理系统 Mock API 服务</h1>
            <p>服务状态: <span style="color: green;">● 运行中</span></p>
            <p>访问 <a href="/docs">/docs</a> 查看接口文档</p>
            <p>访问 <a href="/login-page">/login-page</a> 进入模拟登录页面（供 UI 测试）</p>
            <hr>
            <h2>可用接口</h2>
            <ul>
                <li><b>POST /api/login</b> - 用户登录</li>
                <li><b>GET /api/employees</b> - 查询员工列表（支持分页、搜索）</li>
                <li><b>GET /api/users</b> - 查询用户列表（同 employees）</li>
                <li><b>POST /api/approval</b> - 提交审批申请</li>
                <li><b>GET /api/approvals</b> - 查询审批记录</li>
            </ul>
        </body>
    </html>
    """

@app.get("/login-page", response_class=HTMLResponse)
async def login_page():
    """模拟登录页面 - 供 Playwright UI 测试使用"""
    return """
    <html>
        <head>
            <title>企业管理系统登录</title>
            <style>
                body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
                .login-box { width: 350px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { text-align: center; margin-bottom: 20px; }
                input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                button:hover { background: #40a9ff; }
                #error-msg { color: red; margin-top: 10px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>企业管理系统</h2>
                <input type="text" id="username" placeholder="用户名" value="test001">
                <input type="password" id="password" placeholder="密码" value="123456">
                <button id="login-btn" onclick="doLogin()">登 录</button>
                <div id="error-msg"></div>
            </div>
            <script>
                async function doLogin() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error-msg');
                    try {
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username, password })
                        });
                        const data = await response.json();
                        if (data.code === 0) {
                            errorDiv.style.color = 'green';
                            errorDiv.innerText = '登录成功！Token: ' + data.data.token.substring(0,20) + '...';
                            // 跳转到员工列表页
                            setTimeout(() => { window.location.href = '/employee-page'; }, 1000);
                        } else {
                            errorDiv.style.color = 'red';
                            errorDiv.innerText = data.message;
                        }
                    } catch (e) {
                        errorDiv.innerText = '网络错误';
                    }
                }
            </script>
        </body>
    </html>
    """

@app.get("/employee-page", response_class=HTMLResponse)
async def employee_page():
    """模拟员工查询页面 - 供 Playwright UI 测试使用"""
    return """
    <html>
        <head>
            <title>员工管理</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #f0f2f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
                h1 { margin-bottom: 20px; }
                .search-box { margin-bottom: 20px; }
                input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 250px; }
                button { padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background: #fafafa; }
                #loading, #error { text-align: center; padding: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>👥 员工信息管理</h1>
                <div class="search-box">
                    <input type="text" id="keyword" placeholder="输入姓名或部门搜索">
                    <button id="search-btn" onclick="searchEmployees()">搜 索</button>
                    <button onclick="resetSearch()">重 置</button>
                    <span style="margin-left: 20px;">页码: <input type="number" id="page" value="1" min="1" style="width: 60px;"> 
                    每页: <select id="size"><option>2</option><option>10</option><option>20</option><option>50</option></select>
                    <button onclick="searchEmployees()">跳转</button></span>
                </div>
                <div id="table-container">
                    <table id="employee-table">
                        <thead>
                            <tr><th>ID</th><th>姓名</th><th>部门</th><th>职位</th><th>电话</th><th>邮箱</th><th>状态</th></tr>
                        </thead>
                        <tbody id="table-body">
                            <tr><td colspan="7" id="loading">加载中...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div id="pagination-info"></div>
            </div>
            <script>
                async function searchEmployees() {
                    const keyword = document.getElementById('keyword').value;
                    const page = document.getElementById('page').value;
                    const size = document.getElementById('size').value;
                    const tbody = document.getElementById('table-body');
                    tbody.innerHTML = '<tr><td colspan="7">加载中...</td></tr>';
                    try {
                        let url = `/api/employees?page=${page}&size=${size}`;
                        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
                        const resp = await fetch(url);
                        const data = await resp.json();
                        if (data.code === 0) {
                            renderTable(data.data.items);
                            document.getElementById('pagination-info').innerText = 
                                `共 ${data.data.total} 条，第 ${data.data.page}/${data.data.total_pages} 页`;
                        } else {
                            tbody.innerHTML = '<tr><td colspan="7" style="color:red;">加载失败</td></tr>';
                        }
                    } catch (e) {
                        tbody.innerHTML = '<tr><td colspan="7" style="color:red;">网络错误</td></tr>';
                    }
                }
                function renderTable(items) {
                    const tbody = document.getElementById('table-body');
                    if (items.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7">暂无数据</td></tr>';
                        return;
                    }
                    let html = '';
                    items.forEach(emp => {
                        html += `<tr><td>${emp.id}</td><td>${emp.name}</td><td>${emp.department}</td>
                                 <td>${emp.position}</td><td>${emp.phone}</td><td>${emp.email}</td><td>${emp.status}</td></tr>`;
                    });
                    tbody.innerHTML = html;
                }
                function resetSearch() {
                    document.getElementById('keyword').value = '';
                    document.getElementById('page').value = 1;
                    searchEmployees();
                }
                window.onload = searchEmployees;
            </script>
        </body>
    </html>
    """

# ---------- API 接口 ----------

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录接口
    - 正常登录：返回 token
    - 错误密码：返回 401 业务码
    - 账号锁定：返回 403 业务码
    """
    username = request.username
    password = request.password

    # 检查是否锁定账号
    if username in locked_users:
        return JSONResponse(
            status_code=403,
            content={"code": 403, "message": "账号已被锁定，请联系管理员", "data": None}
        )

    # 验证用户名密码
    if username not in valid_users:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "message": "用户名或密码错误", "data": None}
        )

    user_info = valid_users[username]
    if user_info["password"] != password:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "message": "用户名或密码错误", "data": None}
        )

    # 登录成功，生成 token
    token = generate_token(username)
    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "token": token,
            "username": username,
            "role": user_info["role"]
        }
    }

@app.get("/api/employees")
async def get_employees(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="搜索关键词（姓名/部门）")
):
    """
    员工查询接口
    - 支持分页：page, size
    - 支持关键词搜索：keyword（匹配姓名或部门）
    """
    # 过滤数据
    filtered = employees_data
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            emp for emp in employees_data
            if keyword_lower in emp["name"].lower() or keyword_lower in emp["department"].lower()
        ]

    # 分页
    paginated = paginate_items(filtered, page, size)

    return {
        "code": 0,
        "message": "success",
        "data": paginated
    }


@app.put("/api/employees")
async def update_employee(payload: EmployeeUpdateRequest):
    """
    更新员工信息（mock 用）
    - 仅更新内存 employees_data，便于 UI/E2E 用例验证“修改后刷新可见”
    """
    updated = False
    for emp in employees_data:
        if emp.get("name") == payload.name:
            if payload.department is not None:
                emp["department"] = payload.department
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="employee not found")

    return {"code": 0, "message": "updated", "data": {"name": payload.name}}

@app.get("/api/users")
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None)
):
    """
    用户查询接口（别名，与 employees 逻辑一致）
    """
    return await get_employees(page, size, keyword)

@app.post("/api/approval", response_model=ApprovalResponse)
async def create_approval(request: ApprovalRequest):
    """
    提交审批申请接口
    - 返回申请单号
    """
    global next_approval_id
    approval_id = f"AP{next_approval_id:06d}"
    next_approval_id += 1

    # 构建审批记录
    record = {
        "id": approval_id,
        "applicant": request.applicant,
        "type": request.approval_type,
        "content": request.content,
        "amount": request.amount,
        "status": "pending",
        "create_time": datetime.now().isoformat()
    }
    approvals_data.append(record)

    return {
        "code": 0,
        "message": "申请已提交",
        "data": {
            "approval_id": approval_id,
            "status": "pending"
        }
    }

@app.get("/api/approvals")
async def get_approvals(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    applicant: Optional[str] = Query(None)
):
    """
    查询审批记录接口
    """
    filtered = approvals_data
    if applicant:
        filtered = [a for a in approvals_data if a["applicant"] == applicant]

    paginated = paginate_items(filtered, page, size)
    return {
        "code": 0,
        "message": "success",
        "data": paginated
    }

# ---------- 启动服务 ----------
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 启动企业管理系统 Mock API 服务")
    print("📍 访问地址: http://127.0.0.1:8000")
    print("📚 API 文档: http://127.0.0.1:8000/docs")
    print("🔐 测试账号: test001 / 123456")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)