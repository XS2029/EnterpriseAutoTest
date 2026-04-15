"""
YAML 数据读取工具
用于读取测试数据文件，支持按用例名提取数据
"""

import os
import yaml
from typing import List, Dict, Any, Optional


class YAMLReader:
    """YAML 文件读取器"""

    def __init__(self, base_path: str = None):
        """
        初始化读取器
        :param base_path: YAML 文件的基础路径，默认为项目 data/yaml 目录
        """
        if base_path is None:
            # 自动定位到项目 data/yaml 目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.base_path = os.path.join(project_root, "data", "yaml")
        else:
            self.base_path = base_path

    def read_yaml(self, file_name: str) -> List[Dict[str, Any]]:
        """
        读取单个 YAML 文件，返回完整数据列表
        :param file_name: YAML 文件名（例如 "login_data.yaml"）
        :return: 解析后的数据列表
        """
        file_path = os.path.join(self.base_path, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    print(f"警告：文件 {file_name} 内容为空")
                    return []
                print(f"成功读取文件：{file_name}，包含 {len(data)} 条用例数据")
                return data
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            raise
        except yaml.YAMLError as e:
            print(f"错误：YAML 解析失败 - {e}")
            raise

    def get_test_data(self, file_name: str, case_name: str) -> Optional[Dict[str, Any]]:
        """
        根据用例名提取单条测试数据
        :param file_name: YAML 文件名
        :param case_name: 用例名称（casename 字段的值）
        :return: 匹配的用例数据字典，未找到则返回 None
        """
        all_data = self.read_yaml(file_name)
        for case in all_data:
            if case.get("casename") == case_name:
                print(f"找到用例：{case_name}")
                return case
        print(f"警告：未找到用例 '{case_name}'")
        return None

    def get_test_data_by_index(self, file_name: str, index: int) -> Optional[Dict[str, Any]]:
        """
        根据索引提取测试数据（用于参数化）
        :param file_name: YAML 文件名
        :param index: 数据索引（从0开始）
        :return: 用例数据字典
        """
        all_data = self.read_yaml(file_name)
        if 0 <= index < len(all_data):
            return all_data[index]
        print(f"警告：索引 {index} 超出范围，文件共有 {len(all_data)} 条数据")
        return None

    def get_all_casenames(self, file_name: str) -> List[str]:
        """
        获取文件中所有用例名称
        :param file_name: YAML 文件名
        :return: 用例名称列表
        """
        all_data = self.read_yaml(file_name)
        return [case.get("casename", "未命名用例") for case in all_data]


# ---------- 便捷函数（模块级调用）----------
_default_reader = YAMLReader()

def read_yaml(file_name: str) -> List[Dict[str, Any]]:
    """读取 YAML 文件的便捷函数"""
    return _default_reader.read_yaml(file_name)

def get_test_data(file_name: str, case_name: str) -> Optional[Dict[str, Any]]:
    """根据用例名提取数据的便捷函数"""
    return _default_reader.get_test_data(file_name, case_name)


# ---------- 测试代码 ----------
if __name__ == "__main__":
    print("=" * 50)
    print("测试 YAML 读取工具")
    print("=" * 50)

    # 创建测试用的临时 YAML 文件
    test_file = "test_temp.yaml"
    test_path = os.path.join(_default_reader.base_path, test_file)
    test_data = [
        {
            "casename": "测试用例1",
            "module": "测试模块",
            "request": {"method": "GET", "url": "/test1"},
            "validate": [{"eq": ["status_code", 200]}]
        },
        {
            "casename": "测试用例2",
            "module": "测试模块",
            "request": {"method": "POST", "url": "/test2"},
            "validate": [{"eq": ["json.code", 0]}]
        }
    ]

    # 写入测试文件
    with open(test_path, "w", encoding="utf-8") as f:
        yaml.dump(test_data, f, allow_unicode=True, default_flow_style=False)
    print(f"📝 已创建测试文件：{test_file}")

    # 测试读取功能
    reader = YAMLReader()
    all_data = reader.read_yaml(test_file)
    print(f"\n读取到的数据条数：{len(all_data)}")

    case_names = reader.get_all_casenames(test_file)
    print(f"用例名称列表：{case_names}")

    single_case = reader.get_test_data(test_file, "测试用例2")
    if single_case:
        print(f"\n提取到的单条用例：\n{yaml.dump(single_case, allow_unicode=True)}")

    # 清理测试文件
    os.remove(test_path)
    print(f"\n🧹 已清理测试文件：{test_file}")
    print("\n✅ YAML 读取工具测试通过！")