"""
项目配置文件
包含数据库连接参数、测试环境配置等
"""

# 允许通过环境变量覆盖（便于 CI/本地启动不同端口）
import os

# MySQL 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "test_enterprise",
    "charset": "utf8mb4",
    "autocommit": True,  # 自动提交事务
    "cursorclass": "DictCursor",  # 返回字典格式，方便断言
}

# Mock API 服务配置
MOCK_API_URL = os.getenv("MOCK_API_URL", "http://127.0.0.1:8000")

# 测试配置
TEST_CONFIG = {
    "api_timeout": 10,  # API 请求超时时间（秒）
    "ui_timeout": 30,   # UI 元素等待超时时间（秒）
    "response_time_warning": 500,  # 响应时间警告阈值（毫秒）
}