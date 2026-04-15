"""
日志工具模块
基于 loguru 配置，支持控制台输出、文件滚动保存、不同级别日志分类
"""

import os
import sys
from loguru import logger

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取日志目录路径
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 移除默认的 handler
logger.remove()

# 1. 控制台输出（INFO级别及以上）
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 2. 全部日志文件（DEBUG级别及以上），按天滚动，保留7天
logger.add(
    os.path.join(LOG_DIR, "all_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="00:00",      # 每天午夜滚动
    retention="7 days",    # 保留7天
    encoding="utf-8",
    enqueue=True           # 异步写入
)

# 3. 错误日志单独文件（ERROR级别及以上）
logger.add(
    os.path.join(LOG_DIR, "error_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="00:00",
    retention="30 days",
    encoding="utf-8",
    enqueue=True
)

# 4. 测试用例专用日志（用于测试执行跟踪）
logger.add(
    os.path.join(LOG_DIR, "test_execution_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
    rotation="00:00",
    retention="7 days",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: "test" in record["extra"].get("category", "")
)


def get_logger(name: str = None):
    """
    获取 logger 实例，可绑定模块名称
    """
    if name:
        return logger.bind(name=name)
    return logger


class LogContext:
    """
    日志上下文管理器，用于在特定代码块中添加额外信息
    """
    def __init__(self, **kwargs):
        self.context = kwargs
        self._token = None

    def __enter__(self):
        # logger.contextualize 返回的是上下文管理器，需要显式进入
        self._token = logger.contextualize(**self.context)
        self._token.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            self._token.__exit__(exc_type, exc_val, exc_tb)


# ---------- 测试代码 ----------
if __name__ == "__main__":
    print("=" * 50)
    print("测试 Loguru 日志配置")
    print("=" * 50)

    logger.info("这是一条INFO级别日志，会输出到控制台和all日志文件")
    logger.debug("这是一条DEBUG级别日志，只写入all日志文件")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志，会写入error日志文件")

    # 测试带分类的日志
    logger.bind(category="test").info("这是测试执行日志，会单独记录到test_execution文件")

    # 测试上下文管理器
    with LogContext(case_name="test_demo", user="test001"):
        logger.info("在上下文中记录的日志，包含额外字段")

    print("\n✅ 日志配置测试完成，请查看 logs/ 目录下的日志文件")
    print(f"日志目录：{LOG_DIR}")