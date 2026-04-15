"""
测试执行入口
封装 pytest 命令，支持选择测试范围、生成 Allure 报告
"""

import os
import sys
import subprocess
import argparse
import shutil
import json
import urllib.request
import zipfile
import io

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_tests(test_target="all", allure_dir="./reports/allure-results", verbose=True):
    """
    执行测试
    :param test_target: 测试目标，可选 "all", "api", "login", "query", "submit"
    :param allure_dir: Allure 结果输出目录
    :param verbose: 是否详细输出
    """
    # 构建 pytest 命令
    cmd = ["pytest"]

    # 选择测试范围
    if test_target == "all":
        cmd.append("test_cases/api/")
    elif test_target == "api":
        cmd.append("test_cases/api/")
    elif test_target == "login":
        cmd.append("test_cases/api/test_login.py")
    elif test_target == "query":
        cmd.append("test_cases/api/test_query.py")
    elif test_target == "submit":
        cmd.append("test_cases/api/test_submit.py")
    else:
        print(f"未知测试目标: {test_target}")
        return

    # 添加 Allure 参数
    cmd.append(f"--alluredir={allure_dir}")

    # 添加详细输出
    if verbose:
        cmd.append("-v")
        cmd.append("-s")

    print("=" * 60)
    print(f"执行测试命令: {' '.join(cmd)}")
    print("=" * 60)

    # 执行命令
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def generate_report(results_dir="./reports/allure-results",
                    report_dir="./reports/allure-report",
                    clean=True,
                    auto_install=False):
    """
    生成 Allure HTML 报告
    :param results_dir: Allure 结果目录
    :param report_dir: 报告输出目录
    :param clean: 是否清理旧报告
    :param auto_install: 未检测到 Allure CLI 时是否自动下载（Windows 友好）
    """
    allure_exe = _resolve_allure_cli(auto_install=auto_install)
    if allure_exe is None:
        print("⚠️ 未检测到可用的 Allure CLI，已跳过报告生成。")
        print("   你仍然已生成 Allure 结果文件（allure-results），但缺少 CLI 无法生成 HTML 报告。")
        print("   可选方案：安装 Allure CLI（推荐）或使用 --auto-install-allure 自动下载。")
        return 0

    cmd = [allure_exe, "generate", results_dir, "-o", report_dir]
    if clean:
        cmd.append("--clean")

    print("=" * 60)
    print(f"生成报告命令: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("⚠️ Allure CLI 看似存在，但执行失败（WinError 2）。已跳过报告生成。")
        print("   建议：重新安装/修复 Allure CLI，或使用 --auto-install-allure 自动下载。")
        return 0


def open_report(report_dir="./reports/allure-report"):
    """
    打开 Allure 报告
    :param report_dir: 报告目录
    """
    allure_exe = _resolve_allure_cli(auto_install=False)
    if allure_exe is None:
        print("⚠️ 未检测到 Allure CLI（allure 命令不存在），已跳过打开报告。")
        return 0

    cmd = [allure_exe, "open", report_dir]
    print("=" * 60)
    print(f"打开报告命令: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("⚠️ Allure CLI 执行失败（WinError 2），已跳过打开报告。")
        return 0


def _resolve_allure_cli(auto_install: bool = False) -> str | None:
    """
    返回可执行的 Allure CLI 路径（优先使用系统 PATH，其次可选自动下载到本地 tools）。
    """
    exe = shutil.which("allure")
    if exe:
        return exe
    if not auto_install:
        return None

    try:
        return _ensure_local_allure_cli()
    except Exception as e:
        print(f"⚠️ 自动下载 Allure CLI 失败：{e}")
        return None


def _ensure_local_allure_cli() -> str:
    """
    自动下载 Allure CLI（zip）并解压到 ./tools/allure/ 下，返回其中的 allure.bat 路径。
    - 仅做最小依赖：urllib + zipfile（标准库）
    """
    tools_dir = os.path.join(PROJECT_ROOT, "tools", "allure")
    os.makedirs(tools_dir, exist_ok=True)

    # 若已存在可执行文件，直接复用
    existing = os.path.join(tools_dir, "allure-2", "bin", "allure.bat")
    if os.path.exists(existing):
        return existing

    # 从 GitHub 获取 latest release 资产并下载 zip
    api_url = "https://api.github.com/repos/allure-framework/allure2/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "EnterpriseAutoTest",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    assets = data.get("assets") or []
    zip_asset = None
    for a in assets:
        name = (a.get("name") or "").lower()
        if name.endswith(".zip") and "allure" in name:
            zip_asset = a
            break
    if not zip_asset or not zip_asset.get("browser_download_url"):
        raise RuntimeError("未找到 Allure zip 下载资源（GitHub latest assets 为空或格式变化）")

    download_url = zip_asset["browser_download_url"]
    print("=" * 60)
    print(f"未检测到 Allure CLI，开始自动下载: {download_url}")
    print("=" * 60)

    req2 = urllib.request.Request(download_url, headers={"User-Agent": "EnterpriseAutoTest"})
    with urllib.request.urlopen(req2, timeout=120) as resp2:
        zip_bytes = resp2.read()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(tools_dir)

    # 解压后目录一般形如 allure-2.x.y/；我们创建一个稳定软路径 tools/allure/allure-2 -> 解压目录
    extracted_dirs = [
        os.path.join(tools_dir, d)
        for d in os.listdir(tools_dir)
        if os.path.isdir(os.path.join(tools_dir, d)) and d.lower().startswith("allure-2")
    ]
    if not extracted_dirs:
        raise RuntimeError("解压完成但未找到 allure-2* 目录")
    extracted_dirs.sort(key=lambda p: len(p))  # 优先较短（通常是 allure-2.x.y）
    extracted = extracted_dirs[0]

    stable_dir = os.path.join(tools_dir, "allure-2")
    if os.path.exists(stable_dir) and os.path.isdir(stable_dir):
        # 若之前残留，清理后再重建（尽量不做递归删除以避免误删；只在 stable_dir 是空目录时删除）
        try:
            if not os.listdir(stable_dir):
                os.rmdir(stable_dir)
        except Exception:
            pass

    if not os.path.exists(stable_dir):
        # Windows 上没有 symlink 权限时，退化为复制目录成本较高；这里用“重命名”优先，失败则直接使用 extracted
        try:
            os.rename(extracted, stable_dir)
            extracted = stable_dir
        except Exception:
            pass

    exe = os.path.join(extracted, "bin", "allure.bat")
    if not os.path.exists(exe):
        raise RuntimeError("未找到 bin/allure.bat（下载包结构变化或解压失败）")
    return exe


def main():
    parser = argparse.ArgumentParser(description="企业级自动化测试框架执行入口")
    parser.add_argument("--target", "-t", default="all",
                        choices=["all", "api", "login", "query", "submit"],
                        help="测试目标范围")
    parser.add_argument("--run-only", "-r", action="store_true",
                        help="仅运行测试，不生成报告")
    parser.add_argument("--report-only", action="store_true",
                        help="仅生成并打开报告（基于已有测试结果）")
    parser.add_argument("--allure-dir", default="./reports/allure-results",
                        help="Allure 结果输出目录")
    parser.add_argument("--report-dir", default="./reports/allure-report",
                        help="报告输出目录")
    parser.add_argument("--auto-install-allure", action="store_true",
                        help="未检测到 Allure CLI 时自动下载（生成 Allure HTML 报告用）")

    args = parser.parse_args()

    if args.report_only:
        # 仅生成并打开报告
        if generate_report(args.allure_dir, args.report_dir, auto_install=args.auto_install_allure) == 0:
            open_report(args.report_dir)
    else:
        # 运行测试
        exit_code = run_tests(args.target, args.allure_dir)
        if exit_code != 0:
            print("\n⚠️ 测试执行失败，请检查错误信息")
            sys.exit(exit_code)

        # 生成并打开报告
        if not args.run_only:
            if generate_report(args.allure_dir, args.report_dir, auto_install=args.auto_install_allure) == 0:
                open_report(args.report_dir)


if __name__ == "__main__":
    main()