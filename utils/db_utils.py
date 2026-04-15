"""
数据库操作工具类
封装 PyMySQL 的常用操作，提供连接管理、查询、增删改等功能
"""

import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_CONFIG


class MySQLHelper:
    """MySQL 数据库操作助手类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化数据库连接配置
        :param config: 数据库配置字典，默认使用 settings.py 中的 DB_CONFIG
        """
        self.config = config if config else DB_CONFIG
        self.connection = None
        self.cursor = None

    def get_connection(self):
        """
        获取数据库连接
        :return: 数据库连接对象
        """
        if self.connection is None or not self.connection.open:
            try:
                self.connection = pymysql.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    user=self.config["user"],
                    password=self.config["password"],
                    database=self.config["database"],
                    charset=self.config["charset"],
                    autocommit=self.config.get("autocommit", True),
                    cursorclass=DictCursor
                )
                print(f"数据库连接成功: {self.config['host']}:{self.config['port']}/{self.config['database']}")
            except Exception as e:
                print(f"数据库连接失败: {e}")
                raise
        return self.connection

    def get_cursor(self):
        """
        获取游标对象
        :return: 游标对象
        """
        if self.cursor is None:
            self.cursor = self.get_connection().cursor()
        return self.cursor

    def execute_query(self, sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句（SELECT）
        :param sql: SQL 查询语句
        :param params: 参数元组，用于参数化查询
        :return: 查询结果列表（每行为字典格式）
        """
        try:
            cursor = self.get_cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            result = cursor.fetchall()
            print(f"查询成功，返回 {len(result)} 条记录")
            return result
        except Exception as e:
            print(f"查询失败: {e}")
            raise

    def execute_update(self, sql: str, params: Tuple = None) -> int:
        """
        执行更新语句（INSERT/UPDATE/DELETE）
        :param sql: SQL 更新语句
        :param params: 参数元组，用于参数化查询
        :return: 受影响的行数
        """
        try:
            cursor = self.get_cursor()
            if params:
                affected_rows = cursor.execute(sql, params)
            else:
                affected_rows = cursor.execute(sql)
            self.connection.commit()
            print(f"✏️ 更新成功，影响 {affected_rows} 行")
            return affected_rows
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            self.connection.rollback()
            raise

    def execute_many(self, sql: str, params_list: List[Tuple]) -> int:
        """
        批量执行更新语句
        :param sql: SQL 更新语句
        :param params_list: 参数元组列表
        :return: 受影响的总行数
        """
        try:
            cursor = self.get_cursor()
            affected_rows = cursor.executemany(sql, params_list)
            self.connection.commit()
            print(f"✏️ 批量更新成功，影响 {affected_rows} 行")
            return affected_rows
        except Exception as e:
            print(f"❌ 批量更新失败: {e}")
            self.connection.rollback()
            raise

    def close(self):
        """关闭游标和数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
            print("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动关闭连接"""
        self.close()


# ---------- 测试代码 ----------
if __name__ == "__main__":
    # 测试数据库连接和基本操作
    db = MySQLHelper()
    try:
        db.get_connection()
        
        # 测试查询
        print("\n--- 测试查询 users 表 ---")
        users = db.execute_query("SELECT * FROM users LIMIT 5")
        for user in users:
            print(f"  {user['id']}: {user['username']} ({user['status']})")
        
        print("\n--- 测试查询 employees 表（技术部） ---")
        tech_employees = db.execute_query(
            "SELECT * FROM employees WHERE department = %s",
            ("技术部",)
        )
        print(f"  技术部员工数: {len(tech_employees)}")
        
        print("\n--- 测试查询 approvals 表（pending 状态） ---")
        pending = db.execute_query(
            "SELECT * FROM approvals WHERE status = %s",
            ("pending",)
        )
        print(f"  待审批记录数: {len(pending)}")
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        db.close()