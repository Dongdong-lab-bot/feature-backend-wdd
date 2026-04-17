from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(msg: str) -> None:
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(msg: str) -> None:
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg: str) -> None:
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def print_info(msg: str) -> None:
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")


SEED_SCRIPTS: List[Tuple[str, str, bool]] = [
    ("reset_dev_db_from_models", "重置数据库表结构", True),
    ("seed_demo_ledger_data", "台账演示数据", False),
    ("seed_inspection_demo", "巡检演示数据", False),
    ("seed_ledger_templates", "台账模板数据", False),
]


def load_script_module(script_name: str):
    script_path = Path(__file__).parent / f"{script_name}.py"
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


async def run_single_seed(script_name: str, description: str) -> bool:
    print_info(f"正在执行: {description} ({script_name}.py)")

    module = load_script_module(script_name)
    if module is None:
        print_error(f"加载脚本失败: {script_name}.py")
        return False

    if not hasattr(module, "main"):
        print_error(f"脚本没有 main 函数: {script_name}.py")
        return False

    try:
        main_func = getattr(module, "main")
        if asyncio.iscoroutinefunction(main_func):
            await main_func()
        else:
            main_func()
        print_success(f"执行成功: {description}")
        return True
    except Exception as e:
        print_error(f"执行失败: {description} - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_seeds() -> None:
    print_header("Safefood 测试数据生成工具")
    print_info("开始批量执行数据插入脚本...\n")

    success_count = 0
    fail_count = 0

    for script_name, description, required in SEED_SCRIPTS:
        success = await run_single_seed(script_name, description)
        if success:
            success_count += 1
        else:
            fail_count += 1
            if required:
                print_error("关键脚本执行失败，终止后续操作")
                break

    print_header("执行结果汇总")
    print_success(f"成功: {success_count} 个脚本")
    if fail_count > 0:
        print_error(f"失败: {fail_count} 个脚本")
    else:
        print_info("所有脚本执行完成！")


if __name__ == "__main__":
    asyncio.run(run_all_seeds())