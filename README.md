# EnterpriseAutoTest - 企业级接口与UI自动化测试框架

## 项目简介
本项目是一个基于 Pytest + Playwright 的自动化测试框架，旨在模拟企业级应用的接口测试与 Web UI 测试全流程。项目包含 Mock API 服务、数据驱动测试、数据库断言、Allure 可视化报告及 Jenkins 持续集成等核心模块。

## 技术栈
- **核心框架**：Pytest
- **Web自动化**：Playwright
- **接口测试**：Requests + Pytest
- **数据驱动**：YAML + Excel
- **数据库**：MySQL + PyMySQL
- **报告**：Allure
- **持续集成**：Jenkins / GitHub Actions
- **Mock服务**：FastAPI

## 目录结构
（此处可粘贴前文的目录结构树）

## 快速开始
1. 克隆本项目
2. 创建并激活虚拟环境：`python -m venv venv` → `venv\Scripts\activate`
3. 安装依赖：`pip install -r requirements.txt`
4. 安装浏览器驱动：`playwright install`
5. 启动 Mock 服务：`python mock_server/mock_api.py`
6. 运行测试：`pytest -v`

## 作者
HJL - 华东理工大学 智能科学与技术专业 2026届