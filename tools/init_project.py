"""
项目初始化脚本

根据项目规范和配置文件，自动化新项目的初始化过程。
"""

import os
import shutil
import argparse
import logging

# from datetime import datetime  # unused

from config_loader import get_config
from utils import get_project_root
from utils import ensure_dir_exists, execute_command

# 配置日志
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

CONFIG = None
PROJECT_ROOT = None


def load_app_config():
    """加载项目配置。"""
    global CONFIG, PROJECT_ROOT
    try:
        CONFIG = get_config()
        PROJECT_ROOT = get_project_root()
        if not CONFIG or not PROJECT_ROOT:
            logger.error(
                "项目配置加载失败，请检查 config_loader.py 和 project_config.yaml"
            )
            raise SystemExit("配置加载失败")
        logger.info(f"项目配置加载成功。项目根目录: {PROJECT_ROOT}")
    except Exception as e:
        logger.error(f"加载配置时发生错误: {e}", exc_info=True)
        raise SystemExit("配置加载异常")


def create_core_directories(target_project_root):
    """根据配置创建核心目录结构。"""
    logger.info(f"开始在 {target_project_root} 创建核心目录结构...")
    if not CONFIG:
        logger.error("配置未加载，无法创建目录。")
        return False

    # 从目录结构标准清单或配置中获取核心目录
    # 简化处理：直接从 project_config.yaml 的 structure_check.standard_list_file 指向的文件解析
    # 或者直接在 project_config.yaml 中定义一个核心目录列表
    # 此处暂时硬编码一个示例列表，后续应从配置动态获取
    # core_dirs_from_config = CONFIG.get(
    #     "structure_check", {}).get("standard_list_file")  # unused
    # 实际应解析 standard_list_file 来获取目录，这里简化
    # 假设 standard_list_file 中有明确的目录列表，或者在 config 中直接定义
    # 例如，在 project_config.yaml 中增加一个 section:
    # init_project:
    #   core_directories:
    #     - "docs/01-设计"
    #     - "docs/02-开发"
    #     - "project/src"
    #     - "project/tests"
    #     - "logs"
    #     - "tools"
    #     - "bak"

    # 优先从配置的 init_project.core_directories 获取
    core_directories = CONFIG.get("init_project", {}).get("core_directories", [])

    if not core_directories:
        # 如果配置中没有，则尝试从目录结构标准清单中提取（简化版）
        # 这是一个更复杂的解析，暂时使用一个预设列表
        logger.warning(
            "配置中未找到 'init_project.core_directories'，将使用预设核心目录列表。"
        )
        # 从配置文件获取报告目录
        report_dir = CONFIG.get("structure_check", {}).get(
            "report_dir", "logs/检查报告"
        )

        core_directories = [
            "docs/01-设计",
            "docs/02-开发",
            "docs/03-管理",
            "docs/04-接口",
            "docs/05-用户",
            "docs/04-模板",
            report_dir,
            "project/.devcontainer",
            "project/.github/workflows",
            "project/.vscode",
            "project/config",
            "project/public",
            "project/scripts",
            "project/src/components",
            "project/src/services",
            "project/src/types",
            "project/src/utils",
            "project/tests/integration",
            "project/tests/unit",
            "tools/tests",
            "bak/专项备份",
            "bak/待清理文件",
            "bak/日常备份",
        ]

    created_count = 0
    for rel_dir in core_directories:
        abs_dir_path = os.path.join(target_project_root, rel_dir)
        try:
            ensure_dir_exists(abs_dir_path)
            logger.info(f"已创建或确认目录存在: {abs_dir_path}")
            created_count += 1
        except Exception as e:
            logger.error(f"创建目录 {abs_dir_path} 失败: {e}", exc_info=True)

    if created_count == len(core_directories):
        logger.info("核心目录结构创建成功。")
        return True
    else:
        logger.warning(
            f"核心目录创建部分完成: {created_count}/{len(core_directories)} 个目录已创建。"
        )
        return False


def main():
    """脚本主入口。"""
    parser = argparse.ArgumentParser(description="项目初始化脚本")
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="新项目的名称 (将作为新项目根目录的子目录名，在当前项目根目录下创建)",
    )
    parser.add_argument(
        "--target-path",
        type=str,
        default=None,
        help="可选：指定新项目的完整根路径。如果提供，将忽略 --name 和当前项目结构。",
    )

    args = parser.parse_args()

    load_app_config()  # 首先加载配置

    if args.target_path:
        new_project_root = os.path.abspath(args.target_path)
        logger.info(f"使用指定的目标路径: {new_project_root}")
    else:
        if not PROJECT_ROOT:
            logger.error("无法确定当前项目根目录，无法创建新项目。")
            return
        new_project_root = os.path.join(PROJECT_ROOT, args.name)
        logger.info(f"将在当前项目下创建新项目: {new_project_root}")

    if os.path.exists(new_project_root):
        logger.warning(
            f"目标路径 {new_project_root} 已存在。请确保这是一个安全的操作或选择其他路径。"
        )
        # 可以增加确认步骤或直接退出
        # choice = input("路径已存在，是否继续？ (y/n): ").lower()
        # if choice != 'y':
        #     logger.info("操作已取消。")
        #     return
    else:
        try:
            ensure_dir_exists(new_project_root)
            logger.info(f"成功创建新项目根目录: {new_project_root}")
        except Exception as e:
            logger.error(
                f"创建新项目根目录 {new_project_root} 失败: {e}", exc_info=True
            )
            return

    # 1. 创建核心目录
    if not create_core_directories(new_project_root):
        logger.error("核心目录创建失败，初始化中止。")
        return

    # 1. 创建核心目录
    if not create_core_directories(new_project_root):
        logger.error("核心目录创建失败，初始化中止。")
        return

    # 2. 创建核心文件
    if not create_core_files(new_project_root):
        logger.error("核心文件创建失败，初始化中止。")
        return

    # 3. 初始化 Git 仓库
    if not initialize_git_repository(new_project_root):
        logger.warning("Git 仓库初始化失败。请检查是否安装了 Git。")
    else:
        logger.info("Git 仓库初始化成功。")

    logger.info(
        f"项目 {args.name or os.path.basename(new_project_root)} 初始化基本完成。"
    )


def create_core_files(target_project_root):
    """根据配置创建核心文件。"""
    logger.info(f"开始在 {target_project_root} 创建核心文件...")
    if not CONFIG:
        logger.error("配置未加载，无法创建文件。")
        return False

    # 从配置中获取核心文件列表及其可选内容模板
    # 例如，在 project_config.yaml 中增加一个 section:
    # init_project:
    #   core_files:
    #     - path: "README.md"
    #       content: "# {project_name}\n\nProject description here."
    #     - path: ".gitignore"
    #       template: "default_gitignore_template.txt" # 指向一个模板文件
    #     - path: "project/src/__init__.py"
    #       content: "" # 创建空文件
    #     - path: "docs/03-管理/project_config.yaml"
    #       copy_from: "docs/03-管理/project_config.yaml" # 从当前项目复制
    #     - path: "docs/03-管理/.env.example"
    #       copy_from: "docs/03-管理/.env.example"

    core_files_config = CONFIG.get("init_project", {}).get("core_files", [])
    if not core_files_config:
        logger.warning(
            "配置中未找到 'init_project.core_files'，将使用预设核心文件列表。"
        )
        # 预设一些基本文件
        project_name_placeholder = os.path.basename(target_project_root)
        core_files_config = [
            {
                "path": "README.md",
                "content": f"# {project_name_placeholder}\n\n这是一个新的项目。",
            },
            {
                "path": ".gitignore",
                "content": (
                    "# Common .gitignore\n__pycache__/\n*.pyc\n*.pyo\n"
                    "*.pyd\n.Python\nbuild/\ndist/\n*.egg-info/\n.env\n"
                    ".vscode/\n.idea/\nlogs/\nbak/\n*.log\n*.sqlite3\n"
                    "*.db\n*.tmp\n*.swp\n.DS_Store"
                ),
            },
            {
                "path": "docs/03-管理/.env.example",
                "copy_from_project_root": ("docs/03-管理/.env.example"),
            },
            {
                "path": "docs/03-管理/project_config.yaml",
                "copy_from_project_root": ("docs/03-管理/project_config.yaml"),
            },
            {"path": "project/src/__init__.py", "content": ""},
            {"path": "project/tests/__init__.py", "content": ""},
            {"path": "tools/__init__.py", "content": ""},
            {"path": "tools/tests/__init__.py", "content": ""},
        ]

    created_count = 0
    for file_entry in core_files_config:
        rel_file_path = file_entry.get("path")
        if not rel_file_path:
            logger.warning(f"配置文件条目缺少 'path': {file_entry}")
            continue

        abs_file_path = os.path.join(target_project_root, rel_file_path)
        abs_file_dir = os.path.dirname(abs_file_path)

        try:
            ensure_dir_exists(abs_file_dir)  # 确保文件所在目录存在

            if "copy_from_project_root" in file_entry:
                source_rel_path = file_entry["copy_from_project_root"]
                source_abs_path = os.path.join(PROJECT_ROOT, source_rel_path)
                if os.path.exists(source_abs_path):
                    shutil.copy2(source_abs_path, abs_file_path)
                    logger.info(f"已从 {source_abs_path} 复制文件到: {abs_file_path}")
                else:
                    logger.warning(
                        f"源文件 {source_abs_path} 不存在，无法复制。将创建空文件于 {abs_file_path}"
                    )
                    with open(
                        abs_file_path,
                        "w",
                        encoding=CONFIG.get("general", {}).get(
                            "default_encoding", "utf-8"
                        ),
                    ) as f:
                        f.write("")  # 创建空文件作为回退
            elif "content" in file_entry:
                content = file_entry["content"]
                # 简单替换项目名占位符
                project_name_actual = os.path.basename(target_project_root)
                content = content.replace("{project_name}", project_name_actual)
                with open(
                    abs_file_path,
                    "w",
                    encoding=CONFIG.get("general", {}).get("default_encoding", "utf-8"),
                ) as f:
                    f.write(content)
                logger.info(f"已创建文件: {abs_file_path}")
            else:
                # 默认创建空文件
                with open(
                    abs_file_path,
                    "w",
                    encoding=CONFIG.get("general", {}).get("default_encoding", "utf-8"),
                ) as f:
                    f.write("")
                logger.info(f"已创建空文件: {abs_file_path}")

            created_count += 1
        except Exception as e:
            logger.error(f"创建或复制文件 {abs_file_path} 失败: {e}", exc_info=True)

    if created_count == len(core_files_config):
        logger.info("核心文件创建成功。")
        return True
    else:
        logger.warning(
            f"核心文件创建部分完成: {created_count}/{len(core_files_config)} 个文件已创建/复制。"
        )
        return False


def initialize_git_repository(target_project_root):
    """在目标路径初始化Git仓库。"""
    logger.info(f"尝试在 {target_project_root} 初始化Git仓库...")
    try:
        # 检查 .git 目录是否已存在
        if os.path.exists(os.path.join(target_project_root, ".git")):
            logger.info(f"路径 {target_project_root} 下已存在 .git 目录，跳过初始化。")
            return True

        result = execute_command("git", ["init"], cwd=target_project_root, check=False)
        completed_process = (
            result  # Keep variable name if other logic depends on it,
            # or adapt
        )
        if result and result.returncode == 0:
            logger.info("Git仓库初始化成功。")
            # 可以选择进行初次提交
            # execute_command("git", ["add", "."], cwd=target_project_root,
            #                 check=True)  # Or check=False and handle result
            # execute_command("git", ["commit", "-m",
            #                 "Initial commit by project initializer"],
            #                 cwd=target_project_root, check=True)
            return True
        else:
            logger.error(
                f"Git init 命令执行失败，返回码: {completed_process.returncode}"
            )
            logger.error(f"错误输出: {completed_process.stderr}")
            return False
    except FileNotFoundError:
        logger.error(
            "Git 命令未找到。请确保 Git 已安装并配置在系统 PATH 中。", exc_info=True
        )
        return False
    except Exception as e:
        logger.error(f"初始化Git仓库时发生错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":

    main()
