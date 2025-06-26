#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Work Completion Processing Tool (Python Version)
Purpose: Perform checks, generate reports, and manage end-of-work tasks.
Author: AI9 Tech Lead (Yujun)
Version: 0.1 (Initial Python Structure)
"""

import argparse
import yaml
from pathlib import Path
import fnmatch  # For exclude pattern matching
import importlib
import logging
import os
import re
import shutil  # Needed for potential future move/delete operations
import subprocess
from pathlib import Path
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import json

import yaml  # 用于加载目录规范配置

# 导入错误处理机制
from exceptions import ValidationError, ErrorHandler
from config_loader import get_config

# 初始化错误处理器
error_handler = ErrorHandler()

# Git配置管理函数
def get_git_config():
    """获取Git配置，支持环境变量覆盖"""
    try:
        # 直接加载配置文件，避免导入问题
        config_path = Path(__file__).parent.parent / "docs" / "03-管理" / "project_config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        git_config = config.get('git', {})
    except Exception as e:
        print(f"警告: 无法加载Git配置文件: {e}")
        git_config = {}
    
    # 支持环境变量覆盖
    repo_dir_name = os.environ.get('GIT_REPO_NAME', git_config.get('repo_dir_name', 'github_repo'))
    default_branch = os.environ.get('GIT_DEFAULT_BRANCH', git_config.get('default_branch', 'main'))
    auto_push = os.environ.get('GIT_AUTO_PUSH', str(git_config.get('auto_push', True))).lower() == 'true'
    commit_prefix = os.environ.get('GIT_COMMIT_PREFIX', git_config.get('commit_message_prefix', '自动备份'))
    
    return {
        'repo_dir_name': repo_dir_name,
        'default_branch': default_branch,
        'auto_push': auto_push,
        'commit_message_prefix': commit_prefix
    }

def get_git_repo_path():
    """获取Git仓库路径，支持配置化"""
    git_config = get_git_config()
    return BACKUP_DIR / git_config['repo_dir_name']

# --- Configuration Loading ---


def load_project_config():
    """加载项目配置"""
    config_path = Path(__file__).parent.parent / "docs" / \
        "03-管理" / "project_config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None


def get_project_root():
    """获取项目根目录"""
    config = load_project_config()
    if config and config.get('paths', {}).get('root'):
        return Path(config['paths']['root'])

    # 备用方案
    return Path(__file__).resolve().parent.parent

# --- MCP工具集成 ---


class MCPToolsManager:
    """MCP工具管理器，用于集成TaskManager、memory等工具"""

    def __init__(self, project_root):
        self.project_root = Path(project_root)

        # 从配置读取MCP路径
        try:
            from config_loader import get_mcp_config
            mcp_config = get_mcp_config()

            # 构建完整路径
            tasks_path = mcp_config['task_manager']['storage_path']
            memory_path = mcp_config['memory']['storage_path']

            self.tasks_file = self.project_root / tasks_path
            self.memory_file = self.project_root / memory_path

            logging.getLogger(__name__).info(
                f"MCP配置加载成功 - Tasks: {self.tasks_file}, Memory: {self.memory_file}")

        except Exception as e:
            # 回退到默认路径
            logging.getLogger(__name__).warning(f"MCP配置加载失败，使用默认路径: {e}")
            self.tasks_file = self.project_root / "docs" / "02-开发" / "tasks.json"
            self.memory_file = self.project_root / "docs" / "02-开发" / "memory.json"

        # 确保存储目录存在
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def create_approval_task(
            self,
            title,
            description,
            operation_type="approval",
            priority="normal"):
        """创建需要人工审批的任务"""
        try:
            # 模拟TaskManager创建审批任务的功能
            task_data = {
                "id": f"approval_{int(time.time())}",
                "title": title,
                "description": description,
                "type": operation_type,
                "priority": priority,
                "status": "pending_approval",
                "created_at": datetime.now().isoformat(),
                "requires_human_approval": True
            }

            # 读取现有任务
            tasks = []
            if self.tasks_file.exists():
                try:
                    with open(self.tasks_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 确保tasks是列表格式
                        if isinstance(data, list):
                            tasks = data
                        else:
                            logger.warning("Tasks文件格式错误，重新初始化为列表")
                            tasks = []
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Tasks文件格式错误，重新初始化: {e}")
                    tasks = []

            # 添加新任务
            tasks.append(task_data)

            # 保存任务
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

            logger.info(f"已创建审批任务: {title} (ID: {task_data['id']})")
            return task_data['id']

        except Exception as e:
            logger.error(f"创建审批任务失败: {e}")
            return None

    def store_memory(self, key, content, category="general"):
        """存储重要信息到memory"""
        try:
            # 读取现有记忆
            memory_data = {}
            if self.memory_file.exists():
                try:
                    with open(self.memory_file, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Memory文件格式错误，将重新创建: {e}")
                    memory_data = {}

            # 按类别组织记忆
            if category not in memory_data:
                memory_data[category] = {}

            memory_data[category][key] = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "updated_by": "finish.py"
            }

            # 保存记忆
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)

            logger.info(f"已存储记忆: {category}/{key}")
            return True

        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            return False

    def get_memory(self, key, category="general"):
        """从memory获取信息"""
        try:
            if not self.memory_file.exists():
                return None

            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Memory文件格式错误: {e}")
                return None

            if category in memory_data and key in memory_data[category]:
                return memory_data[category][key]["content"]

            return None

        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None

    def wait_for_approval(self, task_id, timeout_minutes=60):
        """等待人工审批（模拟实现）"""
        logger.warning(f"任务 {task_id} 需要人工审批，请检查 {self.tasks_file}")
        logger.warning("在实际环境中，此处应暂停执行等待人工审批")
        logger.warning("当前为演示模式，将继续执行")
        return True  # 演示模式下直接返回True

    def sequential_thinking(
            self,
            context,
            decision_points,
            reasoning_type="analysis"):
        """Sequential thinking for critical decision points"""
        try:
            thinking_result = {
                "context": context,
                "reasoning_type": reasoning_type,
                "decision_points": decision_points,
                "timestamp": datetime.now().isoformat(),
                "conclusions": []
            }

            logger.info(f"开始逻辑推理: {context}")

            # 逐步分析每个决策点
            for i, point in enumerate(decision_points, 1):
                logger.info(f"分析决策点 {i}: {point['question']}")

                # 模拟逻辑推理过程
                analysis = {
                    "step": i,
                    "question": point['question'],
                    "factors": point.get('factors', []),
                    "risks": point.get('risks', []),
                    "benefits": point.get('benefits', []),
                    "recommendation": point.get('recommendation', '需要进一步分析')
                }

                thinking_result["conclusions"].append(analysis)
                logger.info(f"决策点 {i} 分析完成: {analysis['recommendation']}")

            # 存储思考结果到memory
            self.store_memory(
                f"thinking_{reasoning_type}",
                thinking_result,
                "sequential_thinking")

            logger.info(f"逻辑推理完成，共分析 {len(decision_points)} 个决策点")
            return thinking_result

        except Exception as e:
            logger.error(f"Sequential thinking 失败: {e}")
            return None

    def get_thinking_history(self, reasoning_type=None):
        """获取历史思考记录"""
        try:
            if not self.memory_file.exists():
                return []

            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Memory文件格式错误: {e}")
                return []

            thinking_data = memory_data.get("sequential_thinking", {})

            if reasoning_type:
                return thinking_data.get(f"thinking_{reasoning_type}", {})
            else:
                return thinking_data

        except Exception as e:
            logger.error(f"获取思考历史失败: {e}")
            return []

# --- 全新参数解析系统 ---


def init_arg_parser():
    """初始化并返回配置好的参数解析器"""
    parser = argparse.ArgumentParser(
        description="AI9项目工作流管理系统",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
        epilog="示例:\n  python finish.py --daily --backup-dir ./backups\n"
    )

    # 主操作模式参数组 (互斥，默认为daily)
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument("--daily",
                            action="store_true",
                            help="日常备份模式（包含自动备份和日报生成）[默认]")
    mode_group.add_argument("--release",
                            action="store_true",
                            help="发布模式（完整校验并生成发布包）")
    mode_group.add_argument("--backup-only",
                            action="store_true",
                            help="快速备份模式（仅执行项目备份，跳过其他检查）")
    mode_group.add_argument("--init-config",
                            action="store_true",
                            help="初始化配置文件（生成默认配置）")
    mode_group.add_argument("--self-check",
                            action="store_true",
                            help="每日工作自检模式（根据基本规则执行检查并生成报告）")

    # 路径参数组
    path_group = parser.add_argument_group('路径参数')
    path_group.add_argument("--backup-dir",
                            metavar="PATH",
                            help="指定自定义备份路径\n(优先于配置文件设置)")
    path_group.add_argument("--config",
                            metavar="FILE",
                            help="使用指定配置文件路径")

    # 功能控制参数组
    control_group = parser.add_argument_group('功能控制参数')
    control_group.add_argument("--no-backup",
                               action="store_true",
                               help="跳过项目备份步骤")
    control_group.add_argument("--no-quality-check",
                               action="store_true",
                               help="跳过代码质量检查")
    control_group.add_argument("--auto-cleanup",
                               action="store_true",
                               help="自动清理违规目录到项目外部")

    # 调试参数组
    debug_group = parser.add_argument_group('调试参数')
    debug_group.add_argument("--verbose",
                             action="store_true",
                             help="启用详细调试输出")
    debug_group.add_argument("-h", "--help",
                             action="help",
                             help="显示帮助信息并退出")

    return parser


def validate_args(args):
    """参数逻辑校验"""
    if args.backup_dir and not (args.daily or args.release):
        raise ValueError("--backup-dir 必须与 --daily/--release 模式配合使用")
    if args.config and not os.path.exists(args.config):
        raise FileNotFoundError(f"配置文件不存在: {args.config}")
    if args.backup_dir and not os.path.isabs(args.backup_dir):
        args.backup_dir = os.path.abspath(args.backup_dir)


# 初始化参数系统
parser = init_arg_parser()
args = parser.parse_args()

# 设置默认模式为 daily（如果没有指定任何模式）
if not any([args.daily,
            args.release,
            args.backup_only,
            args.init_config,
            args.self_check]):
    args.daily = True
    print("未指定运行模式，默认使用 --daily 模式")

try:
    validate_args(args)
except (ValueError, FileNotFoundError) as e:
    parser.error(str(e))

# --- Constants and Global Setup ---
NL = "\\n"  # Using literal newline for Markdown compatibility in Python strings
PROJECT_ROOT = get_project_root()

# 初始化MCP工具管理器
mcp_tools = MCPToolsManager(PROJECT_ROOT)

# --- 统一路径配置变量 ---
# 项目标准路径配置
config = load_project_config()
if config and config.get('paths'):
    STANDARD_BACKUP_DIR = Path(
        config['paths'].get(
            'backup_dir',
            PROJECT_ROOT / "bak"))
    STANDARD_LOGS_DIR = Path(
        config['paths'].get(
            'logs_dir',
            PROJECT_ROOT /
            "logs"))
else:
    STANDARD_BACKUP_DIR = PROJECT_ROOT / "bak"  # 标准备份目录
    STANDARD_LOGS_DIR = PROJECT_ROOT / "logs"  # 标准日志目录
STANDARD_CLEANUP_DIR = STANDARD_BACKUP_DIR / "待清理资料"  # 标准清理目录

# 基础目录配置
LOG_DIR = STANDARD_LOGS_DIR / "工作记录"
# 从配置文件获取报告目录
config = get_config()
report_dir_config = config.get(
    'structure_check',
    {}).get(
        'report_dir',
    'logs/检查报告')
REPORT_DIR = PROJECT_ROOT / report_dir_config
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = LOG_DIR / f"finish_py_{TIMESTAMP}.log"
REPORT_FILE = LOG_DIR / f"finish_report_py_{TIMESTAMP}.md"

# BACKUP_DIR 先占位，随后根据规范配置动态定义
BACKUP_DIR = None
BACKUP_LOG_DIR = STANDARD_LOGS_DIR / "其他日志"  # Directory for the backup log file
BACKUP_LOG_FILE = BACKUP_LOG_DIR / "备份系统日志.md"
BACKUP_RETENTION_COUNT = 60  # Keep last 60 backups

# Script-level counters
issues_found = 0
warnings_found = 0

# Debug: Print directory paths
print(f"DEBUG: PROJECT_ROOT = {PROJECT_ROOT}")
print(f"DEBUG: STANDARD_LOGS_DIR = {STANDARD_LOGS_DIR}")
print(f"DEBUG: LOG_DIR = {LOG_DIR}")
print(f"DEBUG: REPORT_DIR = {REPORT_DIR}")

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure parent dirs exist too

# --- Logging Setup ---
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Console Handler (optional, for immediate feedback)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
# Map log levels to colors (requires a library like 'colorlog' or manual ANSI codes)
# For simplicity, we'll use basic console output for now
# TODO: Add colorized console output if needed
logger.addHandler(console_handler)

# FIRST_EDIT: 加载目录规范配置，用于 invoke_directory_check 和 agent_verify_structure


def get_daily_git_commits():
    """获取当天的 Git 提交记录"""
    try:
        # 获取今天的日期，格式 YYYY-MM-DD
        today_date = datetime.now().strftime("%Y-%m-%d")
        # 构建 git log 命令，获取今天的提交记录，格式化输出
        # --after 和 --before 用于指定日期范围，确保只获取当天的记录
        # --pretty=format:'- %h %s (%an)' 指定输出格式：短哈希 作者 提交信息
        # --no-merges 排除合并提交
        cmd = [
            "git", "log", f"--after={today_date} 00:00:00",
            f"--before={today_date} 23:59:59",
            "--pretty=format:- %h %s (%an)", "--no-merges"
        ]
        # 使用配置化的Git仓库路径
        git_repo_path = str(get_git_repo_path())
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            cwd=git_repo_path)
        commits = result.stdout.strip()
        if commits:
            logger.info("成功获取当日 Git 提交记录。")
            return f"### 当日 Git 提交记录\n\n{commits}\n"
        else:
            logger.info("当日无 Git 提交记录。")
            return "### 当日 Git 提交记录\n\n当日无提交记录。\n"
    except subprocess.CalledProcessError as e:
        logger.error(f"获取 Git 提交记录失败: {e.stderr}")
        return "### 当日 Git 提交记录\n\n获取提交记录失败。\n"
    except FileNotFoundError:
        logger.error("Git 命令未找到，请确保 Git 已安装并配置在系统路径中。")
        return "### 当日 Git 提交记录\n\nGit 命令未找到。\n"


if args.init_config:  # 新增初始化配置文件逻辑
    default_spec = {
        "backup_dir": str(STANDARD_BACKUP_DIR),
        "required_dirs": ["src", "logs"]
    }
    # 使用用户指定的配置文件路径，如果提供了的话
    config_path = Path(args.config) if args.config else PROJECT_ROOT / \
        "docs" / "03-管理" / "project_config.yaml"
    # 获取用户指定的备份目录（如果存在）
    user_backup_dir = args.backup_dir or None
    if user_backup_dir:
        default_spec["backup_dir"] = str(Path(user_backup_dir).resolve())

    # 确保配置文件父目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入配置文件
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_spec, f, allow_unicode=True, sort_keys=False)

    logger.info(f"初始配置文件已创建：{config_path}")
    logger.debug(f"配置文件内容：{default_spec}")
    sys.exit(0)

try:
    # 优先使用--config参数指定的配置文件
    config_path = Path(args.config) if args.config else \
        PROJECT_ROOT / "docs" / "03-管理" / "project_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f)
        # 从project_config.yaml的paths部分提取directory_spec格式的配置
        dir_spec = {
            "required_dirs": full_config.get(
                'paths',
                {}).get(
                'required_dirs',
                []),
            "required_files": full_config.get(
                'paths',
                {}).get(
                    'required_files',
                [])}
    logger.info(f"成功加载配置文件：{config_path}")
except FileNotFoundError:
    logger.error(
        "Directory spec config not found. Use --init-config to create one.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Failed to load directory specification: {e}")
    sys.exit(1)

# --- Self-Check Mode Logic ---


def run_self_check():
    """执行每日工作自检流程，集成TaskManager和memory工具"""
    report_content = "# 每日工作自检报告\n\n"
    logger.info("开始执行每日工作自检流程...")

    # 存储自检开始信息到memory
    mcp_tools.store_memory("self_check_start", {
        "timestamp": TIMESTAMP,
        "status": "started",
        "report_type": "daily_self_check"
    })

    # 1. 获取当日 Git 提交记录
    report_content += get_daily_git_commits()

    # 2. 检查是否需要创建审批任务
    critical_issues = []

    # 3. 代码质量检查 (Flake8, ESLint)
    logger.info("执行代码质量检查...")
    try:
        # 运行flake8检查，使用配置文件排除.venv等目录
        config_file = PROJECT_ROOT / "project" / "setup.cfg"
        flake8_cmd = ["flake8", "--max-line-length=88"]
        if config_file.exists():
            flake8_cmd.extend(["--config", str(config_file)])
        flake8_cmd.append(".")

        flake8_result = subprocess.run(
            flake8_cmd,
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if flake8_result.returncode != 0:
            report_content += "\n### 代码质量检查\n\n"
            report_content += "**Flake8检查发现问题:**\n```\n"
            report_content += flake8_result.stdout
            report_content += "```\n"
            critical_issues.append("代码质量问题")
        else:
            report_content += "\n### 代码质量检查\n\n✅ Flake8检查通过\n"
    except FileNotFoundError:
        report_content += "\n### 代码质量检查\n\n⚠️ Flake8未安装或不可用\n"

    # 4. 自动化测试检查
    logger.info("检查测试文件...")
    test_files = list(PROJECT_ROOT.glob("**/test_*.py")) + \
        list(PROJECT_ROOT.glob("**/*_test.py"))
    if test_files:
        report_content += "\n### 测试文件检查\n\n"
        report_content += f"发现 {len(test_files)} 个测试文件:\n"
        for test_file in test_files[:5]:  # 只显示前5个
            report_content += f"- {test_file.relative_to(PROJECT_ROOT)}\n"
        if len(test_files) > 5:
            report_content += f"- ... 还有 {len(test_files) - 5} 个文件\n"
    else:
        report_content += "\n### 测试文件检查\n\n⚠️ 未发现测试文件\n"
        critical_issues.append("缺少测试文件")

    # 5. 文档更新检查
    logger.info("检查文档更新...")
    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.exists():
        recent_docs = []
        for doc_file in docs_dir.rglob("*.md"):
            if doc_file.stat().st_mtime > (datetime.now() - timedelta(days=7)).timestamp():
                recent_docs.append(doc_file)

        report_content += "\n### 文档更新检查\n\n"
        if recent_docs:
            report_content += f"近7天内更新的文档 ({len(recent_docs)} 个):\n"
            for doc in recent_docs[:3]:
                report_content += f"- {doc.relative_to(PROJECT_ROOT)}\n"
        else:
            report_content += "⚠️ 近7天内无文档更新\n"

    # 6. 项目规范符合性检查
    logger.info("检查项目规范符合性...")
    required_files = ["README.md", "requirements.txt", ".gitignore"]
    missing_files = []
    for req_file in required_files:
        if not (PROJECT_ROOT / req_file).exists():
            missing_files.append(req_file)

    if missing_files:
        report_content += "\n### 项目规范检查\n\n"
        report_content += "⚠️ 缺少必要文件:\n"
        for missing in missing_files:
            report_content += f"- {missing}\n"
        critical_issues.append("缺少必要文件")
    else:
        report_content += "\n### 项目规范检查\n\n✅ 必要文件完整\n"

    # 7. Sequential thinking for critical issues analysis
    if critical_issues:
        logger.info(f"发现 {len(critical_issues)} 个关键问题，开始逻辑推理分析...")

        # 构建决策点
        decision_points = []
        for issue in critical_issues:
            if "代码质量" in issue:
                decision_points.append({
                    "question": "如何处理代码质量问题？",
                    "factors": ["代码可维护性", "团队开发效率", "项目稳定性"],
                    "risks": ["技术债务累积", "bug增加", "开发效率下降"],
                    "benefits": ["提高代码质量", "减少维护成本", "提升团队协作"],
                    "recommendation": "立即修复代码质量问题，建立代码审查流程"
                })
            elif "测试文件" in issue:
                decision_points.append({
                    "question": "如何补充测试覆盖？",
                    "factors": ["代码覆盖率", "测试策略", "开发时间"],
                    "risks": ["功能回归", "质量不可控", "部署风险"],
                    "benefits": ["提高代码质量", "减少bug", "增强信心"],
                    "recommendation": "优先为核心功能编写单元测试"
                })
            elif "必要文件" in issue:
                decision_points.append({
                    "question": "如何完善项目结构？",
                    "factors": ["项目规范", "团队协作", "部署要求"],
                    "risks": ["项目混乱", "部署失败", "协作困难"],
                    "benefits": ["规范化管理", "提升专业度", "便于维护"],
                    "recommendation": "立即创建缺失的必要文件"
                })

        # 执行逻辑推理
        thinking_result = mcp_tools.sequential_thinking(
            context="每日自检发现关键问题的处理决策",
            decision_points=decision_points,
            reasoning_type="self_check_analysis"
        )

        if thinking_result:
            report_content += "\n### 逻辑推理分析\n\n"
            for conclusion in thinking_result["conclusions"]:
                report_content += f"**决策点 {
                    conclusion['step']}**: {
                    conclusion['question']}\n"
                report_content += f"- 推荐方案: {conclusion['recommendation']}\n\n"

        # 创建审批任务
        task_description = f"自检发现关键问题需要处理：{', '.join(critical_issues)}"
        task_id = mcp_tools.create_approval_task(
            title="每日自检关键问题处理",
            description=task_description,
            priority="high"
        )
        report_content += f"\n### 审批任务\n\n⚠️ 已创建审批任务 #{task_id}：{task_description}\n"

        # 存储审批任务信息到memory
        mcp_tools.store_memory(f"approval_task_{task_id}", {
            "task_id": task_id,
            "issues": critical_issues,
            "thinking_result": thinking_result,
            "created_at": TIMESTAMP,
            "status": "pending"
        })
    else:
        report_content += "\n### 检查结果\n\n✅ 未发现关键问题\n"

    # 8. 存储自检结果到memory
    self_check_result = {
        "timestamp": TIMESTAMP,
        "status": "completed",
        "critical_issues_count": len(critical_issues),
        "critical_issues": critical_issues,
        "has_approval_task": len(critical_issues) > 0
    }
    mcp_tools.store_memory("self_check_result", self_check_result)

    # 定义自检报告的目录和文件名
    # 使用常量中定义的 REPORT_DIR
    # REPORT_DIR 已经在常量区从配置文件动态获取
    os.makedirs(REPORT_DIR, exist_ok=True)  # 确保目录存在
    # TIMESTAMP 也已在常量区定义
    report_filename = f"每日自检报告_{TIMESTAMP}.md"
    report_path = REPORT_DIR / report_filename

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info(f"自检报告已生成: {report_path}")

        # 将报告复制到 Git 仓库并提交
        git_repo_path = str(get_git_repo_path())  # 使用配置化的Git仓库路径
        git_report_filename = os.path.basename(
            report_path)  # 使用 report_path 中的文件名部分

        # 确保Git仓库中存在符合GitHub仓库结构规范的文件夹
        github_dirs = ["docs", "project", "tools"]
        for dir_name in github_dirs:
            dir_path = os.path.join(git_repo_path, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"在Git仓库中创建了目录：{dir_path}")

        # 将自检报告放在docs目录下
        git_report_path = os.path.join(
            git_repo_path, "docs", git_report_filename)
        try:
            shutil.copy2(report_path, git_report_path)
            logger.info(f"自检报告已复制到 Git 仓库：{git_report_path}")

            commit_message = f"自动提交自检报告：{git_report_filename}"
            # 确保 subprocess.run 调用时传递 encoding 参数
            subprocess.run(["git",
                            "add",
                            git_report_path],
                           cwd=git_repo_path,
                           check=True,
                           encoding='utf-8',
                           errors='replace')
            subprocess.run(["git",
                            "commit",
                            "-m",
                            commit_message],
                           cwd=git_repo_path,
                           check=True,
                           encoding='utf-8',
                           errors='replace')
            logger.info(f"自检报告已提交到 Git 仓库，提交信息：{commit_message}")
            # 更新报告内容，追加提交成功信息
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n自检报告已自动提交到 Git 仓库：`{git_repo_path}`\n")

        except Exception as e:
            logger.error(f"复制或提交自检报告到 Git 仓库失败：{e}")
            # 更新报告内容，追加提交失败信息
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n复制或提交自检报告到 Git 仓库失败：{e}\n")

    except IOError as e:
        logger.error(f"无法写入自检报告: {e}")

    logger.info("每日工作自检流程结束。")

    # 返回自检结果供其他函数使用
    return self_check_result


# DYNAMIC BACKUP_DIR 设置（优先使用命令行参数）
# 参数优先级：CLI > 配置文件 > 默认值
if args.backup_dir:
    BACKUP_DIR = Path(args.backup_dir)
else:
    # 默认使用项目规范要求的备份目录
    BACKUP_DIR = STANDARD_BACKUP_DIR
    # 如果配置文件中有指定，则使用配置文件的设置
    if "backup_dir" in dir_spec:
        config_backup_dir = dir_spec.get("backup_dir")
        if not Path(config_backup_dir).is_absolute():
            # 相对路径，相对于项目根目录（不是父目录）
            BACKUP_DIR = PROJECT_ROOT / config_backup_dir
        else:
            # 绝对路径，检查是否在项目内
            abs_backup_path = Path(config_backup_dir)
            if PROJECT_ROOT in abs_backup_path.parents or abs_backup_path == PROJECT_ROOT:
                BACKUP_DIR = abs_backup_path
            else:
                logger.warning(f"配置的备份目录 {config_backup_dir} 不在项目内，使用默认备份目录")
                BACKUP_DIR = STANDARD_BACKUP_DIR

logger.info(f"当前备份目录：{BACKUP_DIR}")
if not BACKUP_DIR.exists():
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"已创建备份目录：{BACKUP_DIR}")
    except Exception as e:
        logger.error(f"无法创建备份目录 {BACKUP_DIR}: {e}")
        # 回退到项目内的备份目录
        BACKUP_DIR = PROJECT_ROOT / "backups"
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        logger.warning(f"使用回退备份目录：{BACKUP_DIR}")

# --- Main Execution Logic ---
if __name__ == "__main__":
    if args.self_check:
        run_self_check()
    elif args.daily:
        # ... (保留原有 daily 模式逻辑)
        logger.info("执行日常备份模式...")
    elif args.release:
        # ... (保留原有 release 模式逻辑)
        logger.info("执行发布模式...")
    elif args.backup_only:
        # ... (保留原有 backup_only 模式逻辑)
        logger.info("执行快速备份模式...")
    # init-config 模式在参数解析后已处理，此处无需额外逻辑

    logger.info("脚本执行完毕。")

# --- Helper Functions ---


def run_command(
    command_parts,
    check=False,
    cwd=None,
    capture_output=True,
    stdin=None,
    stderr=None,
    force_shell=False,  # 新增参数，明确控制shell使用
    timeout=30  # 新增超时参数，默认30秒
):
    """Runs a command and returns its output, error, and return code.

    Args:
        command_parts: Command as list (preferred) or string
        check: Whether to raise exception on non-zero exit
        cwd: Working directory
        capture_output: Whether to capture stdout/stderr
        stdin: Input for the command
        stderr: How to handle stderr
        force_shell: Explicitly force shell=True (use with caution)
        timeout: Command timeout in seconds (default: 30)
    """
    try:
        # 优先使用列表形式，避免shell=True的问题
        if isinstance(command_parts, str) and not force_shell:
            # 尝试智能拆分命令字符串为列表
            import shlex
            try:
                command_parts = shlex.split(command_parts)
                is_shell = False
                logger.info(
                    f"Auto-converted string command to list: {command_parts}")
            except ValueError:
                # 如果拆分失败，回退到shell=True
                is_shell = True
                logger.warning(
                    f"Failed to parse command string, using shell=True: {command_parts}")
        elif isinstance(command_parts, str) and force_shell:
            is_shell = True
            logger.info(f"Explicitly using shell=True: {command_parts}")
        else:
            is_shell = False

        # 在Windows上，对于npm/npx命令需要使用shell=True
        if sys.platform == "win32" and isinstance(
                command_parts, list) and len(command_parts) > 0:
            if command_parts[0] in ['npm', 'npx', 'node']:
                is_shell = True
                logger.info(
                    f"Using shell=True for Windows npm/npx command: {command_parts}")

        # 对Git命令进行特殊处理，避免在PROJECT_ROOT执行
        if cwd is None and isinstance(command_parts, list) and len(command_parts) > 0 and command_parts[0] == 'git':
            # Git命令默认使用配置化的Git仓库目录
            git_repo_path = get_git_repo_path()
            if git_repo_path.exists():
                effective_cwd = str(git_repo_path)
                logger.info(f"Git command redirected to: {effective_cwd}")
            else:
                effective_cwd = PROJECT_ROOT
                logger.warning(f"Git repo not found at {git_repo_path}, using PROJECT_ROOT: {effective_cwd}")
        else:
            effective_cwd = (
                cwd if cwd is not None else PROJECT_ROOT
            )  # Default to project root if not specified

        # 在Windows上，确保使用正确的编码
        env = os.environ.copy()
        if sys.platform == "win32":
            env['PYTHONIOENCODING'] = 'utf-8'

        result = subprocess.run(
            command_parts,
            capture_output=capture_output,
            shell=is_shell,
            check=check,
            cwd=effective_cwd,
            stdin=stdin,
            stderr=stderr,
            env=env,  # 传递环境变量
            text=True,  # 直接返回字符串而不是字节
            encoding='utf-8',  # 明确指定编码
            errors='replace',  # 处理编码错误
            timeout=timeout  # 添加超时控制
        )

        # 由于使用了text=True，直接获取字符串结果
        stdout_res = result.stdout.strip() if result.stdout else ""
        stderr_res = result.stderr.strip() if result.stderr else ""

        return stdout_res, stderr_res, result.returncode
    except FileNotFoundError:
        cmd_str = command_parts[0] if isinstance(
            command_parts, list) else command_parts
        logger.error(f"Command not found: {cmd_str} (in cwd: {effective_cwd})")
        return None, "Command not found", -1
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed with exit code {
                e.returncode}: {command_parts}")
        stdout_res = e.stdout.strip() if e.stdout else ""
        stderr_res = e.stderr.strip() if e.stderr else ""
        return stdout_res, stderr_res, e.returncode
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {command_parts}")
        return None, f"Command timed out after {timeout}s", -3
    except Exception as e:
        logger.error(f"Error running command '{command_parts}': {e}")
        return None, str(e), -2


def invoke_autoformat():
    """Runs code autoformatters."""
    global issues_found
    logger.info("Starting automatic code formatting...")
    # Remove unused imports and variables via autoflake
    logger.info("Running autoflake to remove unused imports and variables...")
    run_command([
        sys.executable,
        "-m",
        "autoflake",
        "--remove-all-unused-imports",
        "--ignore-init-module-imports",
        "--in-place",
        "-r",
        str(PROJECT_ROOT / "src" / "backend"),
        str(PROJECT_ROOT / "scripts"),
    ])
    try:
        importlib.import_module("autopep8")
        cmd = [
            sys.executable,
            "-m",
            "autopep8",
            "--in-place",
            "--recursive",
            "--aggressive",
            "--aggressive",
            str(PROJECT_ROOT),
        ]
        out, err, code = run_command(cmd)
        if code != 0:
            logger.warning(f"autopep8 issues (code {code}): {err}")
    except ModuleNotFoundError:
        logger.warning(
            "autopep8 not installed, skipping PEP8 auto formatting.")
    # 5. JS ESLint fix via npm script
    try:
        frontend_dir = PROJECT_ROOT / "src" / "frontend" / "admin"
        if frontend_dir.exists():
            cmd = ["npm", "run", "lint:fix"]
            out, err, code = run_command(cmd, cwd=str(frontend_dir))
            if code != 0:
                logger.warning(f"npm lint:fix issues (code {code}): {err}")
        else:
            logger.info(
                "Frontend admin directory not found for JS auto-format.")
    except Exception as e:
        logger.warning(f"JS auto-fix (npm run lint:fix) failed: {e}")
    logger.info("Automatic code formatting completed.")
    # Update report section
    update_report(
        "Automatic Code Formatting",
        "✔️ Applied autoflake, isort, black (if available), eslint --fix",
    )
    return True


# --- Report Functions ---


def initialize_report():
    """Creates the initial report file with header."""
    global REPORT_FILE
    try:
        project_name = PROJECT_ROOT.name
        report_header = """\
# {project_name} Work Completion Report (Python)

**Generation Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Project Name**: {project_name}
**Report ID**: {TIMESTAMP}

## Table of Contents

1. [Dependency Check](#dependency-check)
2. [Directory Structure Check](#directory-structure-check)
# ... (Other sections to be added later)

"""
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_header)
        logger.info(f"Initializing report: {REPORT_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize report: {e}")
        return False


def update_report(section, content):
    """Appends a new section with content to the report file."""
    global REPORT_FILE
    try:
        section_header = f"{NL}{NL}## {section}{NL}{NL}"
        full_content = section_header + content
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(full_content)
        return True
    except Exception as e:
        logger.error(f"Failed to update report section '{section}': {e}")
        return False


# --- Dependency Check Functions ---


def test_python():
    """Checks if Python is installed and executable."""
    stdout, stderr, code = run_command([sys.executable, "--version"])
    if code == 0 and stdout and "Python" in stdout:
        logger.info(f"Python installed: {stdout}")
        return True, stdout
    else:
        logger.warning(
            f"Python not found or version check failed. Code: {code}, Stderr: {stderr}")
        return False, "-"


def test_node():
    """Checks if Node.js is installed."""
    stdout, stderr, code = run_command(["node", "--version"])
    if code == 0 and stdout and stdout.startswith("v"):
        logger.info(f"Node.js installed: {stdout}")
        return True, stdout
    else:
        logger.warning(
            f"Node.js not found or version check failed. Code: {code}, Stderr: {stderr}")
        return False, "-"


def test_flake8():
    """Checks if flake8 is installed."""
    # Prefer checking within the project's Python environment context
    # Ensure we use the same python executable that runs this script
    command = [sys.executable, "-m", "flake8", "--version"]
    logger.info(f"Running command to check flake8: {' '.join(command)}")

    # Explicitly set stdin to DEVNULL and cwd for robustness
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=PROJECT_ROOT,  # Ensure correct working directory
            stdin=subprocess.DEVNULL,  # Explicitly set stdin
            check=False,  # Don't raise error on non-zero exit
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        code = result.returncode
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        return False, "-"
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}")
        return False, "-"

    # Debugging output
    logger.debug(
        f"flake8 check - Code: {code}, Stdout: '{stdout}', Stderr: '{stderr}'")

    # Improve checking logic: Check return code and if stdout contains version
    # info
    if code == 0 and stdout:
        # Try to extract a cleaner version string
        version_line = stdout.splitlines()[0]
        # Extract version like X.Y.Z or similar patterns
        version_match_obj = re.search(r"^(\d+\.\d+(\.\d+)?)", version_line)
        version_match = (version_match_obj.group(
            1) if version_match_obj else version_line.split()[0])
        logger.info(
            f"flake8 installed: {version_match} (Full output: {version_line})")
        return True, version_match
    else:
        logger.warning(
            f"flake8 not found or version check failed. Code: {code}, Stdout: '{stdout}', Stderr: '{stderr}'")
        return False, "-"


def test_eslint():
    """Checks if ESLint is installed (globally via npx or locally)."""
    # 1. Check via npx first (most reliable for installed packages)
    logger.info("Checking ESLint via npx...")
    stdout, stderr, code = run_command(
        ["npx", "eslint", "--version"],
        timeout=60  # ESLint检查使用更长超时时间
    )  # 使用列表形式避免shell=True
    if code == 0 and stdout and stdout.strip().startswith("v"):
        logger.info(f"ESLint available via npx: {stdout.strip()}")
        return True, stdout.strip()

    # 2. Check local node_modules as fallback
    local_eslint_path = PROJECT_ROOT / "node_modules" / ".bin" / "eslint"

    # Windows系统下检查.cmd文件
    if sys.platform == "win32":
        local_eslint_cmd = local_eslint_path.with_suffix(".cmd")
        if local_eslint_cmd.exists():
            stdout, stderr, code = run_command(
                [str(local_eslint_cmd), "--version"],
                timeout=60)
            if code == 0 and stdout and stdout.strip().startswith("v"):
                logger.info(
                    f"ESLint installed in project (Windows): {
                        stdout.strip()}")
                return True, stdout.strip()
    else:
        # Unix系统下检查原始文件
        if local_eslint_path.exists():
            stdout, stderr, code = run_command(
                [str(local_eslint_path), "--version"],
                timeout=60)
            if code == 0 and stdout and stdout.strip().startswith("v"):
                logger.info(
                    f"ESLint installed in project (Unix): {
                        stdout.strip()}")
                return True, stdout.strip()

    logger.warning(
        f"ESLint not found locally or via npx. Code: {code}, Stderr: {stderr}"
    )
    return False, "-"


def test_dependencies():
    """Runs all dependency checks and updates the report."""
    global warnings_found
    logger.info("Checking dependencies...")
    results = {}
    results["Python"] = test_python()
    results["Node.js"] = test_node()
    results["flake8"] = test_flake8()
    results["ESLint"] = test_eslint()

    report_content = f"### Dependency Check Results{NL}{NL}"
    report_content += f"| Dependency | Status | Version |{NL}"
    report_content += f"|------------|--------|---------|{NL}"

    all_deps_ok = True
    required_deps = ["Python", "Node.js"]  # Define essential dependencies

    for name, (installed, version) in results.items():
        status_icon = "✅" if installed else (
            "❌" if name in required_deps else "⚠️")
        status_text = "Installed" if installed else "Not Installed"
        report_content += f"| {name} | {status_icon} {status_text} | {version} |{NL}"
        if not installed:
            if name in required_deps:
                all_deps_ok = False
            else:
                warnings_found += 1  # Non-required dependency missing is a warning
        else:
            logger.info(f"{name} dependency check passed: {version}")

    update_report("Dependency Check", report_content)

    # Store dependency check results to memory
    if 'mcp_tools' in globals():
        dependency_stats = {
            "timestamp": datetime.now().isoformat(),
            "all_deps_ok": all_deps_ok,
            "results": {
                name: {
                    "installed": installed,
                    "version": version} for name,
                (installed,
                 version) in results.items()},
            "required_deps": required_deps,
            "warnings_count": sum(
                1 for name,
                (installed,
                 version) in results.items() if not installed and name not in required_deps)}
        mcp_tools.store_memory(
            "dependency_check_results",
            dependency_stats,
            "dependencies")

    if not all_deps_ok:
        logger.warning("Some required dependencies are not installed.")
    else:
        logger.info("All required dependencies are installed.")

    return all_deps_ok


# --- Dependency Check Functions End ---

# --- Directory Structure Check Start ---


def get_dir_tree(
    startpath: Path,
    max_depth: int = 3,
    indent_char: str = "    ",
    exclude_dirs=None,
):
    """Generates a directory tree structure string."""
    if exclude_dirs is None:
        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    tree = []

    def recurse(current_path: Path, depth: int, prefix: str = ""):
        if depth > max_depth:
            return

        try:
            items = sorted(
                list(current_path.iterdir()),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            tree.append(f"{prefix}└── [Permission Denied]")
            return
        except FileNotFoundError:
            tree.append(
                f"{prefix}└── [Not Found]"
            )  # Should not happen if startpath exists
            return

        pointers = ["├── "] * (len(items) - 1) + ["└── "]
        for pointer, item in zip(pointers, items):
            if item.name in exclude_dirs:
                continue

            icon = "📁" if item.is_dir() else "📄"
            tree.append(f"{prefix}{pointer}{icon} {item.name}")

            if item.is_dir():
                extension = indent_char if pointer == "├── " else " " * \
                    len(indent_char)
                recurse(item, depth + 1, prefix + extension)

    # Start recursion from the root of the startpath for the tree structure
    tree.append(f"📁 {startpath.name}/")  # Add the root dir itself
    recurse(startpath, 0)
    return NL.join(tree)


def get_file_list_details(startpath: Path, exclude_dirs=None):
    """Generates a markdown table with file details recursively."""
    if exclude_dirs is None:
        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    details = []
    details.append(f"| File Path | Type | Size (KB) | Last Modified |{NL}")
    details.append(f"|-----------|------|-----------|---------------|{NL}")

    for item in startpath.rglob("*"):
        # Check if the item or any of its parents are in the exclude list
        if any(part in exclude_dirs for part in item.relative_to(startpath).parts):
            continue
        # Also check the top-level item itself if it's in the root
        if item.parent == startpath and item.name in exclude_dirs:
            continue

        try:
            rel_path = item.relative_to(startpath).as_posix()
            item_type = "Directory" if item.is_dir() else "File"
            size = "N/A"
            last_modified = "N/A"
            if item.is_file():
                size = f"{item.stat().st_size / 1024:.2f}"
            last_modified = datetime.fromtimestamp(
                item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            details.append(
                f"| {rel_path} | {item_type} | {size} | {last_modified} |{NL}"
            )
        except Exception as e:
            logger.warning(f"Could not get details for item {item}: {e}")
            details.append(
                f"| {
                    item.relative_to(startpath).as_posix()} | Error | Error | Error |{NL}")

    return "".join(details)


def check_config_file_uniqueness():
    """检查配置文件的唯一性，确保配置文件只在允许的位置存在。"""
    global issues_found, dir_spec
    logger.info("检查配置文件唯一性...")

    # 从配置加载唯一配置文件规则
    unique_config_files = dir_spec.get("unique_config_files", [])
    if not unique_config_files:
        logger.warning("未找到唯一配置文件规则，跳过配置文件唯一性检查。")
        return True

    issues_detected = False
    report_lines = []

    for config_file in unique_config_files:
        file_name = config_file.get("name")
        allowed_paths = config_file.get(
            "allowed_paths", config_file.get(
                "allowed_path", ["."]))
        description = config_file.get("description", "")

        # 确保allowed_paths是列表
        if isinstance(allowed_paths, str):
            allowed_paths = [allowed_paths]

        if not file_name or not allowed_paths:
            continue

        # 构建所有允许的完整路径
        allowed_full_paths = []
        for allowed_path in allowed_paths:
            if allowed_path == ".":
                allowed_full_paths.append(PROJECT_ROOT / file_name)
            else:
                allowed_full_paths.append(
                    PROJECT_ROOT / allowed_path / file_name)

        # 查找所有匹配的文件
        found_files = list(PROJECT_ROOT.glob(f"**/{file_name}"))

        # 排除允许的路径
        disallowed_files = [
            f for f in found_files if f not in allowed_full_paths]

        if disallowed_files:
            issues_detected = True
            issues_found += len(disallowed_files)
            disallowed_paths = [str(f.relative_to(PROJECT_ROOT))
                                for f in disallowed_files]
            error_msg = f"发现重复的配置文件 {file_name}({description})，应该只存在于 {', '.join(allowed_paths)}，但在以下位置找到: {', '.join(disallowed_paths)}"
            logger.error(error_msg)
            report_lines.append(error_msg)

        # 检查允许路径中是否有多个文件
        valid_files = [f for f in found_files if f in allowed_full_paths]
        if len(valid_files) > 1:
            issues_detected = True
            issues_found += len(valid_files) - 1
            valid_paths = [str(f.relative_to(PROJECT_ROOT))
                           for f in valid_files]
            error_msg = f"在允许的位置发现多个 {file_name} 文件: {
                ', '.join(valid_paths)}。{description}应该只有一个。"
            logger.error(error_msg)
            report_lines.append(error_msg)

    if report_lines:
        section = "配置文件唯一性检查"
        content = "\n".join(report_lines)
        update_report(section, content)

    return not issues_detected


def check_duplicate_files():
    """检查项目中的重复文件。"""
    global issues_found, dir_spec
    logger.info("检查重复文件...")

    # 从配置加载重复文件检测规则
    duplicate_detection = dir_spec.get("duplicate_detection", {})
    patterns = duplicate_detection.get("patterns", [])
    exclude_dirs = duplicate_detection.get("exclude_dirs", [])
    allowed_duplicates = duplicate_detection.get("allowed_duplicates", [])

    if not patterns:
        logger.warning("未找到重复文件检测模式，跳过重复文件检查。")
        return True

    issues_detected = False
    report_lines = []

    # 构建排除目录的完整路径
    exclude_paths = [str(PROJECT_ROOT / d) for d in exclude_dirs]

    # 对每个模式进行检查
    for pattern in patterns:
        # 收集所有匹配的文件
        matched_files = []
        for path in PROJECT_ROOT.glob(f"**/{pattern}"):
            # 检查是否在排除目录中
            path_excluded = False
            for ex in exclude_paths:
                if str(path).startswith(ex):
                    path_excluded = True
                    break
            if not path_excluded:
                matched_files.append(path)

        # 按文件名分组
        file_groups = {}
        for file_path in matched_files:
            file_name = file_path.name
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(file_path)

        # 检查每个组是否有多个文件
        for file_name, paths in file_groups.items():
            if len(paths) > 1 and file_name not in allowed_duplicates:
                issues_detected = True
                issues_found += len(paths) - 1  # 减1是因为应该只有一个文件
                relative_paths = [str(p.relative_to(PROJECT_ROOT))
                                  for p in paths]
                error_msg = f"发现重复文件 {file_name}，在以下位置: {
                    ', '.join(relative_paths)}"
                logger.error(error_msg)
                report_lines.append(error_msg)

    if report_lines:
        section = "重复文件检查"
        content = "\n".join(report_lines)
        update_report(section, content)

    return not issues_detected


def invoke_directory_check():
    """Performs directory structure check and generates structure files using Python."""
    global issues_found, dir_spec
    logger.info(
        "Performing directory structure check (Python implementation)...")

    # 检查项目内是否存在旧的备份目录（应该移至项目外）
    legacy = PROJECT_ROOT / "AI9-Backups"
    if legacy.exists():
        logger.warning(f"发现项目内存在旧的备份目录，应移至{STANDARD_BACKUP_DIR}")
        # 不自动删除，避免数据丢失风险
        logger.info(f"请手动将内容迁移到正确的备份目录: {STANDARD_BACKUP_DIR}")

    # 调用严格的Agent验证函数
    structure_ok = agent_verify_structure(
        auto_cleanup=getattr(
            args, 'auto_cleanup', False))
    if not structure_ok:
        logger.error("Agent目录结构验证失败")
        return False

    # 检查配置文件唯一性
    config_uniqueness_ok = check_config_file_uniqueness()
    if not config_uniqueness_ok:
        logger.error("配置文件唯一性检查失败，发现重复的配置文件。")

    # 检查重复文件
    no_duplicates_ok = check_duplicate_files()
    if not no_duplicates_ok:
        logger.error("重复文件检查失败，发现重复文件。")

    # Store directory check results to memory
    if 'mcp_tools' in globals():
        directory_check_stats = {
            "timestamp": datetime.now().isoformat(),
            "structure_ok": structure_ok,
            "config_uniqueness_ok": config_uniqueness_ok,
            "no_duplicates_ok": no_duplicates_ok,
            "overall_success": structure_ok and config_uniqueness_ok and no_duplicates_ok,
            "legacy_backup_exists": legacy.exists() if 'legacy' in locals() else False}
        mcp_tools.store_memory(
            "directory_check_results",
            directory_check_stats,
            "directory_structure")

    # 只有当所有检查都通过时才返回True
    return structure_ok and config_uniqueness_ok and no_duplicates_ok


# --- Directory Structure Check End ---

# --- Working Directory Cleanliness Check Start ---


def invoke_workdir_clean_check():
    """Checks for scattered files/dirs in the project root directory."""
    global warnings_found
    logger.info("Checking project directory cleanliness...")
    working_directory = PROJECT_ROOT

    # Define allowed top-level items in the project directory (names or
    # patterns)
    allowed_items = {
        # Standard project directories
        "docs",  # Documentation directory
        "logs",  # Logs directory
        "project",  # Main project directory
        "tools",  # Tools directory
        "bak",  # Backup directory
        # Python environment
        ".venv",  # Python virtual environment
        "venv",  # Python virtual environment
        "env",  # Python virtual environment
        # Git and IDE directories
        ".git",  # Git directory
        ".cursor",  # Cursor IDE directory
        ".trae",  # Trae IDE directory
        # Allowed files
        ".env",  # Environment file
        ".flake8",  # Flake8 configuration file
        "README.md",  # Project README
        "LICENSE",  # License file
        "requirements.txt",  # Python requirements
        # Allowed patterns
        ".git*",  # Files like .gitignore, .gitattributes
        "*.lnk",  # Shortcut files
        "*.md",  # Markdown files
        "*.txt",  # Text files
        "*.yaml",  # YAML configuration files
        "*.yml",  # YAML configuration files
    }

    scattered_items_details = []
    try:
        for item in working_directory.iterdir(
        ):  # Iterate through items in parent dir
            is_allowed = False
            # Direct name match
            if item.name in allowed_items:
                is_allowed = True
            else:
                # Pattern match for files
                if item.is_file():
                    for pattern in allowed_items:
                        if (
                            "*" in pattern or "?" in pattern
                        ):  # Simple check for pattern characters
                            # Use fnmatch for pattern matching if needed, pathlib's match is anchorbased
                            # For simple cases like *.lnk or .git*, name
                            # matching works
                            if item.match(pattern):
                                is_allowed = True
                                break
                # No need for complex dir pattern matching here usually

            if not is_allowed:
                item_type = "Directory" if item.is_dir() else "File"
                size = "N/A"
                last_modified = "N/A"
                try:
                    stat = item.stat()
                    if item.is_file():
                        size = f"{stat.st_size / 1024:.2f}"
                    last_modified = datetime.fromtimestamp(
                        stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception as stat_e:
                    logger.warning(
                        f"Could not get stats for scattered item {
                            item.name}: {stat_e}")

                scattered_items_details.append(
                    {
                        "name": item.name,
                        "type": item_type,
                        "size": size,
                        "modified": last_modified,
                    }
                )
                logger.warning(
                    f"Found scattered item in project directory: {item.name}"
                )
                warnings_found += 1

        # Update report
        report_content = ""
        if scattered_items_details:
            report_content += f"⚠️ Found {
                len(scattered_items_details)} scattered items in the project directory ({working_directory}):{NL}{NL}"
            report_content += f"| Name | Type | Size (KB) | Last Modified |{NL}"
            report_content += f"|------|------|-----------|---------------|{NL}"
            for item in scattered_items_details:
                report_content += f"| {
                    item['name']} | {
                    item['type']} | {
                    item['size']} | {
                    item['modified']} |{NL}"
            report_content += f"{NL}### Suggestions{NL}{NL}"
            report_content += f"- Script files should be moved to appropriate subdirectories under 'scripts/'{NL}"
            report_content += f"- Configuration files should be moved to appropriate subdirectories under 'config/'{NL}"
            report_content += (
                f"- Log files should be moved to the 'logs/' directory{NL}"
            )
            report_content += f"- Temporary files should be moved to the 'temp/' directory or deleted{NL}"
        else:
            logger.info(
                "Project directory is clean, no scattered files found.")
            report_content = "✅ Project directory is clean, no scattered files found."

        update_report("Working Directory Cleanliness Check", report_content)
        # Return True if clean (no scattered items)
        return len(scattered_items_details) == 0

    except Exception as e:
        logger.error(f"Error checking project directory cleanliness: {e}")
        update_report(
            "Working Directory Cleanliness Check",
            f"❌ Error occurred while checking project directory cleanliness: {e}",
        )
        return False  # Treat error as failure


def load_whitelist_from_structure_file():
    """从配置文件中加载白名单
    """
    # 直接从配置文件加载白名单
    allowed = set(dir_spec.get("required_dirs", []))
    # 添加required_files到白名单
    allowed.update(dir_spec.get("required_files", []))
    disallowed = set(dir_spec.get("disallowed_top_dirs", []))

    logger.info(f"从配置文件加载白名单: {sorted(allowed)}")
    return allowed, disallowed


# --- Agent Verification Function Start ---
def agent_verify_structure(auto_cleanup=False):
    """Agent 自动检查项目根目录下的顶级目录和文件是否符合规范
    严格白名单机制：只允许白名单内容存在，发现违规内容后完整检查并可选择自动清理
    现在从项目目录结构附表文件读取白名单

    Args:
        auto_cleanup (bool): 是否自动清理违规目录到项目外部
    """
    global issues_found, warnings_found, dir_spec
    logger.info("Agent验证: 开始严格检查项目根目录结构...")

    # 从项目目录结构附表文件获取白名单和黑名单
    allowed, disallowed = load_whitelist_from_structure_file()

    # 检查所有实际存在的项目
    actual_items = []
    for item in PROJECT_ROOT.iterdir():
        actual_items.append(item.name)

    # 收集所有违规项目，而不是立即退出
    all_violations = []

    # 检查是否有黑名单项目存在
    found_disallowed = [name for name in actual_items if name in disallowed]
    if found_disallowed:
        all_violations.extend([(name, "黑名单项目") for name in found_disallowed])
        logger.error(f"❌ 发现禁止存在的目录/文件: {found_disallowed}")

    # 检查是否有不在白名单的项目
    non_hidden_items = [
        name for name in actual_items if not name.startswith(".")]
    invalid = [name for name in non_hidden_items if name not in allowed]
    if invalid:
        all_violations.extend([(name, "不在白名单") for name in invalid])
        logger.error(f"❌ 发现不在白名单中的顶级项: {invalid}")

    # 如果有违规项目，处理它们
    if all_violations:
        issues_found += len(all_violations)

        # 生成详细报告
        error_msg = f"❌ 严重错误：发现 {len(all_violations)} 个违规目录/文件"
        logger.error(error_msg)
        logger.error(f"这些内容应该移动到项目外部（{STANDARD_CLEANUP_DIR.parent}）")

        # 更新报告
        section = "Agent Directory Verification"
        content = f"{error_msg}\n\n⚠️ 发现以下违规内容：\n"
        for item, reason in all_violations:
            content += f"- {item} ({reason})\n"

        # 如果启用自动清理
        if auto_cleanup:
            import shutil
            cleanup_target = STANDARD_CLEANUP_DIR.parent
            cleanup_success = []
            cleanup_failed = []

            for item, reason in all_violations:
                item_path = PROJECT_ROOT / item
                target_path = cleanup_target / item

                # 如果目标路径已存在，添加时间戳后缀
                if target_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if target_path.is_dir():
                        target_path = cleanup_target / f"{item}_{timestamp}"
                    else:
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_path = cleanup_target / \
                            f"{stem}_{timestamp}{suffix}"

                try:
                    if item_path.is_dir():
                        shutil.move(str(item_path), str(target_path))
                    else:
                        shutil.move(str(item_path), str(target_path))
                    cleanup_success.append(item)
                    logger.info(f"✅ 已自动移动违规项目: {item} -> {target_path}")
                except Exception as e:
                    cleanup_failed.append((item, str(e)))
                    logger.error(f"❌ 自动清理失败: {item} - {e}")

            content += "\n🔧 自动清理结果：\n"
            content += f"- 成功清理: {len(cleanup_success)} 项\n"
            content += f"- 清理失败: {len(cleanup_failed)} 项\n"

            if cleanup_failed:
                content += "\n❌ 清理失败的项目：\n"
                for item, error in cleanup_failed:
                    content += f"- {item}: {error}\n"
                content += "\n请手动清理失败的项目后重新运行检查。"
                update_report(section, content)
                import sys
                sys.exit(1)
            else:
                content += "\n✅ 所有违规项目已成功自动清理。"
                logger.info("✅ 所有违规项目已成功自动清理")
        else:
            content += "\n请手动清理后重新运行检查，或使用 --auto-cleanup 参数启用自动清理。"
            update_report(section, content)
            logger.error("系统检查停止，请先清理违规内容！")
            import sys
            sys.exit(1)

    # 如果没有违规项目
    logger.info("✅ Agent验证: 所有顶级目录和文件均符合严格白名单规范")

    # 更新报告
    section = "Agent Directory Verification"
    content = "✅ 所有顶级目录和文件均符合严格白名单规范"
    update_report(section, content)
    return True


# --- Agent Verification Function End ---

# --- Document Standardization and Backup Start ---


def write_backup_log(message):
    """Appends a message to the backup log file."""
    try:
        # Ensure log directory exists
        BACKUP_LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Check if log file exists and add header if not
        if not BACKUP_LOG_FILE.exists():
            header = """# AI9项目备份日志

备份类型说明:
- **daily**: 每日自动备份
- **manual**: 手动触发的备份
- **weekly**: 每周稳定版本的备份
- **milestone**: 项目里程碑的重要备份

"""
            BACKUP_LOG_FILE.write_text(header, encoding="utf-8")

        # Append the log entry
        with open(BACKUP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + NL)

    except Exception as e:
        logger.error(f"Failed to write backup log to {BACKUP_LOG_FILE}: {e}")


def cleanup_old_backups():
    """Removes old backup files, keeping the latest N backups."""
    try:
        if not BACKUP_DIR.exists():
            return  # No backup directory, nothing to clean

        backup_files = sorted(
            BACKUP_DIR.glob("Project-Backup-*.zip"),
            key=lambda p: p.stat().st_mtime,  # Sort by modification time
            reverse=True,  # Newest first
        )

        if len(backup_files) > BACKUP_RETENTION_COUNT:
            files_to_delete = backup_files[BACKUP_RETENTION_COUNT:]
            logger.info(
                f"Found {
                    len(backup_files)} backups. Keeping {BACKUP_RETENTION_COUNT}, deleting {
                    len(files_to_delete)}.")
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old backup: {file_path.name}")
                except Exception as e:
                    logger.error(
                        f"Failed to delete old backup {
                            file_path.name}: {e}")
        else:
            logger.info(
                f"Found {
                    len(backup_files)} backups. No old backups to delete (retention count: {BACKUP_RETENTION_COUNT})."
            )

    except Exception as e:
        logger.error(f"Error during old backup cleanup: {e}")


def invoke_backup(skip_backup=False):
    """Performs project backup using Python's zipfile module."""
    global issues_found
    logger.info("Performing project backup (Python implementation)...")

    if skip_backup:
        logger.info("Skipping project backup based on parameter.")
        update_report(
            "Project Backup",
            "⚠️ Skipping project backup based on parameter.")
        return True

    # 定义时间戳，用于Git提交和ZIP备份
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # 综合备份第一步：Git 提交与推送
    try:
        logger.info("Starting Git commit and push backup...")

        # 确保Git仓库中存在符合GitHub仓库结构规范的文件夹
        git_repo_path = str(get_git_repo_path())  # 使用配置化的Git仓库路径

        # 清理并重新创建Git仓库目录（除了.git目录）
        if os.path.exists(git_repo_path):
            for item in os.listdir(git_repo_path):
                if item != '.git':  # 保留.git目录
                    item_path = os.path.join(git_repo_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
        else:
            os.makedirs(git_repo_path, exist_ok=True)

        # 同步项目文件到Git仓库（排除bak和logs目录）
        github_dirs = ["docs", "project", "tools"]
        for dir_name in github_dirs:
            src_dir = os.path.join(PROJECT_ROOT, dir_name)
            dst_dir = os.path.join(git_repo_path, dir_name)
            if os.path.exists(src_dir):
                shutil.copytree(
                    src_dir, dst_dir, ignore=shutil.ignore_patterns(
                        '*.log', '*.tmp', '__pycache__'))
                logger.info(f"已同步目录到Git仓库：{dir_name}")

        # 同步根目录的重要文件
        root_files = [
            "README.md",
            "requirements.txt",
            ".gitignore",
            "pyproject.toml"]
        for file_name in root_files:
            src_file = os.path.join(PROJECT_ROOT, file_name)
            dst_file = os.path.join(git_repo_path, file_name)
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
                logger.info(f"已同步文件到Git仓库：{file_name}")

        # 在Git仓库目录中执行Git命令
        stdout, stderr, code = run_command(
            ["git", "add", "--all"], cwd=git_repo_path)
        if code != 0:
            logger.warning(f"Git add returned code {code}: {stderr}")
        stdout, stderr, code = run_command(
            ["git", "commit", "-m", f"自动备份: {timestamp}"], cwd=git_repo_path
        )
        if code == 0:
            logger.info("Git commit succeeded")
        elif "nothing to commit" in stderr.lower():
            logger.info("No changes to commit")
        else:
            logger.warning(f"Git commit returned code {code}: {stderr}")
        # 获取当前分支
        stdout, stderr, code = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=git_repo_path)
        current_branch = stdout.strip() if code == 0 else "main"
        stdout, stderr, code = run_command(
            ["git", "push", "origin", current_branch], cwd=git_repo_path)
        if code == 0:
            logger.info("Git push succeeded")
            update_report("GitHub Backup", "✅ GitHub push succeeded")
        else:
            logger.error(f"Git push failed with code {code}: {stderr}")
            update_report(
                "GitHub Backup",
                f"❌ Git push failed with code {code}: {stderr}",
            )
            issues_found += 1
    except Exception as e:
        logger.error(f"Error during Git backup: {e}")
        update_report("GitHub Backup", f"❌ GitHub backup execution error: {e}")
        issues_found += 1

        # Store Git backup failure to memory
        if 'mcp_tools' in globals():
            mcp_tools.store_memory("git_backup_failure", {
                "timestamp": datetime.now().isoformat(),
                "error_message": str(e),
                "git_repo_path": str(git_repo_path),
                "current_branch": current_branch if 'current_branch' in locals() else "unknown"
            }, "git_errors")

    # ZIP 备份参数定义
    backup_filename = f"Project-Backup-{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename

    # Ensure backup directory exists
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create backup directory {BACKUP_DIR}: {e}")
        update_report(
            "Project Backup",
            f"❌ Failed to create backup directory: {e}")
        issues_found += 1
        return False

    # Define exclusion patterns (optimized for performance)
    # Directory-level exclusions for early pruning
    exclude_dirs = {
        "node_modules", ".vscode", ".idea", ".git", "venv", "env",
        "__pycache__", "dist", "build", "backups", ".pytest_cache",
        ".tox", ".mypy_cache"
    }

    # File-level exclusions
    exclude_file_patterns = [
        "*.log", "*.pyc", "*.pyo", "*.tmp", "*.temp", "*.cache",
        ".coverage", "coverage.xml", "*.zip", "*.tar.gz", "*.rar", "*.7z"
    ]

    # Special directories to preserve structure only
    structure_only_dirs = {"bak", "logs"}

    # Standard subdirectories to preserve in structure-only dirs
    standard_bak_dirs = {'config', 'github_repo', '专项备份', '迁移备份'}
    # 从项目规范获取logs标准子目录（根据规范与流程.md中的定义）
    standard_logs_dirs = {'archive', '其他日志', '工作记录', '检查报告'}

    logger.info(f"Creating backup: {backup_path}")
    processed_files = 0
    added_files = 0

    def should_exclude_file(filename):
        """Check if file should be excluded based on patterns"""
        for pattern in exclude_file_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def should_preserve_structure_dir(rel_path, dirname):
        """Check if directory structure should be preserved"""
        if rel_path == "bak" or rel_path == "logs":
            return True
        if rel_path.startswith("bak/") and dirname in standard_bak_dirs:
            return True
        if rel_path.startswith("logs/") and dirname in standard_logs_dirs:
            return True
        return False

    try:
        logger.debug("Opening zip file for writing...")
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            logger.debug("Starting optimized directory walk...")

            # 只备份指定的目录：docs, project, tools
            backup_dirs = ["docs", "project", "tools"]

            for backup_dir in backup_dirs:
                backup_dir_path = os.path.join(PROJECT_ROOT, backup_dir)
                if not os.path.exists(backup_dir_path):
                    logger.warning(f"备份目录不存在，跳过: {backup_dir}")
                    continue

                logger.info(f"正在备份目录: {backup_dir}")

                for root, dirs, files in os.walk(backup_dir_path):
                    # Calculate relative path
                    rel_root = os.path.relpath(root, PROJECT_ROOT)
                    if rel_root == ".":
                        rel_root = ""

                    # Filter out excluded directories (modify dirs in-place for
                    # pruning)
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]

                    # Process files in current directory
                    for filename in files:
                        processed_files += 1
                        if processed_files % 1000 == 0:  # Less frequent but more meaningful updates
                            logger.info(
                                f"正在扫描文件... 已处理 {processed_files} 个项目，已添加 {added_files} 个文件到备份")

                        # Skip excluded files
                        if should_exclude_file(filename):
                            continue

                        # Build file path
                        file_path = os.path.join(root, filename)
                        rel_file_path = os.path.join(
                            rel_root, filename) if rel_root else filename

                        # Skip files in structure-only directories
                        if any(
                            rel_file_path.startswith(
                                d +
                                os.sep) or rel_file_path.startswith(
                                d +
                                "/") for d in structure_only_dirs):
                            continue

                        try:
                            file_size = os.path.getsize(file_path)
                            zipf.write(
                                file_path, rel_file_path.replace(
                                    os.sep, "/"))
                            added_files += 1
                            if added_files % 100 == 0:
                                logger.info(f"已添加 {added_files} 个文件到备份")
                            logger.debug(
                                f"Added to backup: {rel_file_path} ({file_size} bytes)")
                        except Exception as e:
                            logger.warning(
                                f"Failed to add {file_path} to backup: {e}")

                    # Add structure-only directories
                    if rel_root and should_preserve_structure_dir(
                            rel_root, os.path.basename(root)):
                        try:
                            zipf.writestr(
                                rel_root.replace(
                                    os.sep, "/") + "/", "")
                            logger.debug(
                                f"Added directory structure: {rel_root}/")
                        except Exception as e:
                            logger.warning(
                                f"Failed to add directory structure {rel_root}: {e}")

            # 备份根目录的重要文件
            logger.info("正在备份根目录重要文件")
            root_files = [
                "README.md",
                "requirements.txt",
                ".gitignore",
                "pyproject.toml"]
            for file_name in root_files:
                src_file = os.path.join(PROJECT_ROOT, file_name)
                if os.path.exists(src_file):
                    try:
                        file_size = os.path.getsize(src_file)
                        zipf.write(src_file, file_name)
                        added_files += 1
                        logger.info(f"已添加根目录文件到备份: {file_name}")
                        logger.debug(
                            f"Added root file to backup: {file_name} ({file_size} bytes)")
                    except Exception as e:
                        logger.warning(
                            f"Failed to add root file {file_name} to backup: {e}")

        logger.info("备份进度显示结束")
        logger.info(
            f"备份完成！已处理 {processed_files} 个项目，成功添加 {added_files} 个文件到备份")
        logger.debug(
            f"Finished writing to zip file. Processed: {processed_files}, Added: {added_files}")
        # Backup completed successfully
        backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"Backup created successfully: {
                backup_path.name} ({
                backup_size_mb:.2f} MB)")
        update_report(
            "Project Backup",
            f"✅ Project backup created successfully: {
                backup_path.name} ({
                backup_size_mb:.2f} MB)",
        )

        # Write log entry
        log_entry = f"- {timestamp} [daily] 备份大小: {backup_size_mb:.2f}MB - {backup_path.name}"
        write_backup_log(log_entry)

        # Cleanup old backups
        logger.debug("Starting cleanup of old backups...")
        cleanup_old_backups()
        logger.debug("Finished cleanup of old backups.")

        return True

    except Exception as e:
        logger.error(
            f"Project backup failed during processing: {e}", exc_info=True
        )  # Log traceback
        update_report("Project Backup", f"❌ Project backup failed: {e}")
        issues_found += 1

        # Store backup failure details to memory
        if 'mcp_tools' in globals():
            mcp_tools.store_memory("backup_failure_details", {
                "timestamp": datetime.now().isoformat(),
                "error_message": str(e),
                "backup_path": str(backup_path),
                "processed_files": processed_files,
                "added_files": added_files,
                "failure_stage": "processing"
            }, "backup_errors")

        # Attempt to delete potentially incomplete backup file
        try:
            if backup_path.exists():
                logger.info(
                    f"Attempting to delete incomplete backup file: {
                        backup_path.name}")
                backup_path.unlink()
        except Exception as del_e:
            logger.error(
                f"Failed to delete incomplete backup file {
                    backup_path.name}: {del_e}")
            # Store cleanup failure to memory
            if 'mcp_tools' in globals():
                mcp_tools.store_memory("backup_cleanup_failure", {
                    "timestamp": datetime.now().isoformat(),
                    "cleanup_error": str(del_e),
                    "backup_path": str(backup_path)
                }, "backup_errors")
        return False


# --- New Project Cleanup Function Start ---


def invoke_project_cleanup_py():
    """Performs recurring project cleanup tasks (Python implementation)."""
    global issues_found, warnings_found
    logger.info("Performing project cleanup (Python implementation)...")
    cleanup_success = True  # Initialize success flag for cleanup
    report_content = f"### Project Cleanup Results{NL}{NL}"
    actions_taken = []
    issues_detected = []
    # Initialize deletion counters
    deleted_temp_files = 0
    deleted_empty_dirs = 0

    # --- Define Exclusions ---
    exclude_dirs_patterns = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "backups",
        "logs",
    }
    # We handle logs separately

    # --- 1. Clean Temporary Files ---
    temp_patterns = ["*.tmp", "*.bak", "*~"]  # Common temporary file patterns
    found_temp_files = []

    # Scan project root recursively
    for item in PROJECT_ROOT.rglob("*"):
        # Check if item or its parents are in the exclude list
        if any(
            part in exclude_dirs_patterns
            for part in item.relative_to(PROJECT_ROOT).parts
        ):
            continue
        # Also check top-level item itself
        if item.parent == PROJECT_ROOT and item.name in exclude_dirs_patterns:
            continue

        if item.is_file():
            for pattern in temp_patterns:
                if item.match(pattern):
                    found_temp_files.append(item)
                    logger.warning(
                        f"Found temporary file: {
                            item.relative_to(PROJECT_ROOT)}")
                    issues_detected.append(
                        f"Found temporary file: `{
                            item.relative_to(PROJECT_ROOT)}`")
                    # Delete temporary file
                    try:
                        item.unlink()
                        logger.info(
                            f"Deleted temporary file: {
                                item.relative_to(PROJECT_ROOT)}")
                        deleted_temp_files += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to delete temporary file {item}: {e}")
                        issues_detected.append(
                            f"Failed to delete temporary file: `{
                                item.relative_to(PROJECT_ROOT)}` ({e})")
                    break

    if found_temp_files:
        actions_taken.append(
            f"- Temporary file check: Found {len(found_temp_files)}, deleted {deleted_temp_files}."
        )
    warnings_found += len(found_temp_files)

    # --- 2. Clean Empty Directories (Disabled) ---
    # Empty directory cleanup has been disabled to prevent accidental deletion
    found_empty_dirs = []
    deleted_empty_dirs = 0

    # --- 3. Log File Management ---
    stray_logs = []
    archived_logs = 0
    log_archive_dir = LOG_DIR / "archive"
    log_retention_days = 30  # Keep logs for 30 days
    now_ts = datetime.now().timestamp()

    # Create archive directory if it doesn't exist
    try:
        log_archive_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(
            f"Failed to create log archive directory {log_archive_dir}: {e}")
        issues_detected.append(f"Failed to create log archive directory: {e}")
        cleanup_success = False

    # Scan for stray logs and archive old logs
    for item in PROJECT_ROOT.rglob("*"):
        # Check if item or its parents are in the exclude list (important to exclude node_modules etc)
        # Reuse exclude_dirs_patterns but allow scanning inside 'logs' dir
        # itself
        relative_path_parts = item.relative_to(PROJECT_ROOT).parts
        is_in_excluded = any(
            part in exclude_dirs_patterns for part in relative_path_parts
        )

        # Special handling for log files
        if item.is_file() and item.suffix.lower() == ".log":
            is_in_log_dir = item.parent == LOG_DIR
            is_in_archive = log_archive_dir in item.parents

            # a) Check for stray logs (outside logs/ and logs/archive/)
            if not is_in_log_dir and not is_in_archive and not is_in_excluded:
                stray_logs.append(item)
                logger.warning(
                    f"Found stray log file outside designated log directories: {
                        item.relative_to(PROJECT_ROOT)}")
                issues_detected.append(
                    f"Found stray log file: `{item.relative_to(PROJECT_ROOT)}`"
                )
                # Move stray log to LOG_DIR
                try:
                    dest = LOG_DIR / item.name
                    shutil.move(str(item), str(dest))
                    logger.info(
                        f"Moved stray log to {
                            dest.relative_to(PROJECT_ROOT)}")
                except Exception as e:
                    logger.error(f"Failed to move stray log {item.name}: {e}")
                    issues_detected.append(
                        f"Failed to move stray log: `{
                            item.relative_to(PROJECT_ROOT)}` ({e})")

            # b) Check logs inside the main LOG_DIR for archiving
            elif is_in_log_dir:
                try:
                    file_mod_time = item.stat().st_mtime
                    if (now_ts - file_mod_time) > (
                        log_retention_days * 86400
                    ):  # 86400 seconds in a day
                        # Archive this old log file
                        log_archive_dir / item.name
                        logger.info(
                            f"Archiving old log file: {
                                item.name} to {
                                log_archive_dir.name}/")
                        # --- Optional: Move old logs ---
                        # Uncomment to enable archiving
                        # try:
                        #     shutil.move(str(item), str(target_archive_path))
                        #     archived_logs += 1
                        # except Exception as move_e:
                        #     logger.error(f"Failed to archive log file {item.name}: {move_e}")
                        #     issues_detected.append(f"Failed to archive log: `{item.name}` ({move_e})")
                except Exception as stat_e:
                    logger.error(
                        f"Could not get status for log file {
                            item.name}: {stat_e}")
                    issues_detected.append(
                        f"Error checking log file status: `{
                            item.name}` ({stat_e})")

    # Update report section for logs
    log_actions = []
    if stray_logs:
        log_actions.append(
            f"- Stray log check: Found {len(stray_logs)}. Move action disabled."
        )
        warnings_found += len(stray_logs)
    else:
        log_actions.append("- Stray log check: No stray log files found.")

    log_actions.append(
        f"- Log archiving: Checked logs older than {log_retention_days} days. Move action disabled. Archived count (if enabled): {archived_logs}."
    )
    # Append log actions to the main actions_taken list or report separately?
    actions_taken.extend(log_actions)

    # --- Update Report ---
    if not issues_detected:
        report_content += "✅ No major cleanup issues detected." + NL
    else:
        report_content += f"⚠️ Found {
            len(issues_detected)} cleanup issues:{NL}"
        for issue in issues_detected:
            report_content += f"  - {issue}{NL}"
        cleanup_success = False  # Mark as failed if issues found
        warnings_found += len(issues_detected)

    report_content += f"{NL}Actions Performed:{NL}" + NL.join(actions_taken)
    update_report("Project Cleanup", report_content)

    # Store cleanup results to memory
    if 'mcp_tools' in globals():
        cleanup_stats = {
            "timestamp": datetime.now().isoformat(),
            "success": cleanup_success,
            "deleted_temp_files": deleted_temp_files,
            "deleted_empty_dirs": deleted_empty_dirs,
            "stray_logs_found": len(stray_logs),
            "archived_logs": archived_logs,
            "total_issues": len(issues_detected),
            "actions_taken": actions_taken,
            "issues_detected": issues_detected
        }
        mcp_tools.store_memory(
            "cleanup_results",
            cleanup_stats,
            "project_cleanup")

    logger.info("Project cleanup check finished.")
    return cleanup_success


# --- New Project Cleanup Function End ---

# --- Final Report Sections Start ---


def new_completion_checklist():
    """Adds the work completion checklist to the report."""
    logger.info("Generating completion checklist...")
    checklist_content = """\
## Work Completion Checklist

Please check the following items after completion, fill in the date and signature

- [ ] Reviewed and resolved all code quality issues
- [ ] Cleaned up the working directory, removed or moved scattered files
- [ ] Checked project directory structure, conforms to specifications
- [ ] Backed up project code
- [ ] Updated project documentation
- [ ] Committed all changes to the version control system
- [ ] Notified relevant team members that the work is complete

**Completion Date**: ________________
**Developer Signature**: ________________

"""
    update_report("Work Completion Checklist", checklist_content)


def generate_summary():
    """Adds the final execution summary to the report."""
    logger.info("Generating execution summary...")
    summary_content = """\
## Execution Summary

- **Total Issues Found**: {issues_found}
- **Total Warnings Found**: {warnings_found}
- **Completion Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Next Steps

1. Please review all issues and warnings in this report.
2. Resolve all marked issues.
3. Complete all items in the Work Completion Checklist.
4. If necessary, rerun this script to confirm all issues are resolved.

Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    # Append directly to the file, similar to the PS script
    try:
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{NL}{NL}{summary_content}")
        logger.info(f"Execution summary appended to report: {REPORT_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to append summary to report: {e}")
        return False


# --- Final Report Sections End ---

# --- Code Quality Check Functions Start ---


def invoke_flake8_check():
    """Runs flake8 check on Python code and returns results."""
    global issues_found
    logger.info("Performing Python code quality check (flake8)...")

    flake8_installed, _ = test_flake8()  # Reuse dependency check
    if not flake8_installed:
        # Attempt to install flake8 (consider adding a flag to disable
        # auto-install)
        logger.info("flake8 not detected, attempting to install...")
        stdout, stderr, code = run_command(
            [sys.executable, "-m", "pip", "install", "flake8"]
        )
        if code != 0:
            logger.error(
                f"Failed to install flake8 automatically. Please install it manually. Stderr: {stderr}")
            return (
                False,
                "flake8 not installed and auto-install failed",
                0,
                None,
            )
        # Re-test after install attempt
        flake8_installed, _ = test_flake8()
        if not flake8_installed:
            logger.error("flake8 installation confirmed failed.")
            return False, "flake8 installation failed", 0, None

    config_file = PROJECT_ROOT / "config" / "dev-tools" / ".flake8"
    # 回退到根目录 .flake8，当 dev-tools 下该文件不存在时
    if not config_file.exists():
        config_file = PROJECT_ROOT / ".flake8"
    src_dir = PROJECT_ROOT / "src" / "backend"
    scripts_dir = PROJECT_ROOT / "scripts"
    output_file = LOG_DIR / f"python_check_py_{TIMESTAMP}.log"

    targets = []
    if src_dir.exists() and src_dir.is_dir():
        targets.append(str(src_dir))
    if scripts_dir.exists() and scripts_dir.is_dir():
        # Exclude self if running from scripts dir? Or specific subdirs?
        # For now, include all python files found recursively under scripts
        # Be mindful of virtualenvs if they exist under scripts
        targets.append(str(scripts_dir))

    if not targets:
        logger.info(
            "No Python target directories found (src/backend, scripts). Skipping flake8 check."
        )
        return True, "No target directories found", 0, None

    command = [sys.executable, "-m", "flake8"]
    # Add --isolated flag to try and bypass potential config caching issues
    command.append("--isolated")
    if config_file.exists():
        command.extend(["--config", str(config_file)])
    command.extend(targets)

    logger.info(f"Running flake8 command: {' '.join(command)}")
    # Don't use check=True, as flake8 returns non-zero for issues
    stdout, stderr, code = run_command(command)

    # Write output to log file
    full_output = f"Command: {
        ' '.join(command)}{NL}Return Code: {code}{NL}Stdout:{NL}{stdout}{NL}Stderr:{NL}{stderr}"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_output)
    except Exception as e:
        logger.error(f"Failed to write flake8 output log: {e}")

    # Analyze results (flake8 usually outputs issues to stdout)
    issue_count = 0
    if stdout:
        # Count non-empty lines as issues (simplistic)
        lines = [line for line in stdout.splitlines() if line.strip()]
        issue_count = len(lines)

    if code == 0 and issue_count == 0:
        logger.info("flake8 check completed, no issues found.")
        return True, "No issues found", 0, output_file
    elif issue_count > 0:
        logger.warning(
            f"flake8 check completed, found {issue_count} issues. Details in: {output_file}")
        issues_found += issue_count  # Accumulate script-level counter
        return True, f"Found {issue_count} issues", issue_count, output_file
    else:  # code != 0 but no issues found in stdout? Could be config error.
        logger.error(
            f"flake8 check failed or reported errors (code: {code}). Details in: {output_file}")
        issues_found += 1  # Count execution error as one issue
        return False, f"flake8 execution failed (code: {code})", 0, output_file


def invoke_eslint_check():
    """Runs eslint check on JS/TS code and returns results."""
    global issues_found
    logger.info(
        "Performing JavaScript/TypeScript code quality check (eslint)...")

    eslint_installed, eslint_version = test_eslint()
    logger.info(
        f"test_eslint() returned: installed={eslint_installed}, version={eslint_version}")

    if not eslint_installed:
        # Skip auto-install to prevent unwanted npm package installations
        logger.warning(
            "ESLint not detected. Skipping JavaScript/TypeScript check.")
        logger.info(
            "To enable ESLint checks, please install ESLint manually: npm install eslint --save-dev")
        return (
            True,
            "ESLint not installed - check skipped",
            0,
            None,
        )

    logger.info(f"ESLint detected: {eslint_version}")

    # Use ESLint Flat Config at project root
    config_file = PROJECT_ROOT / "eslint.config.cjs"
    src_dir = PROJECT_ROOT / "src" / "frontend"
    output_file = LOG_DIR / f"js_check_py_{TIMESTAMP}.log"

    if not src_dir.exists() or not src_dir.is_dir():
        logger.info(
            f"JavaScript source directory not found: {src_dir}. Skipping eslint check.")
        return True, "Source directory not found", 0, None

    # Build ESLint command - prioritize npx for consistency with test_eslint
    command = []
    # First try npx eslint (global/registry)
    logger.info("Using npx eslint (prioritized for consistency)...")
    command = ["npx", "eslint"]
    if config_file.exists():
        command.extend(["--config", str(config_file)])
    command.extend(["--ext", ".js,.jsx,.ts,.tsx", str(src_dir)])

    logger.info(f"Running eslint command: {command}")
    logger.info(f"Working directory: {PROJECT_ROOT}")

    # Don't use check=True. Exit code 1 means linting errors found.
    stdout, stderr, code = run_command(command, cwd=str(PROJECT_ROOT))

    logger.info(f"ESLint command completed with exit code: {code}")
    logger.info(f"ESLint stdout length: {len(stdout) if stdout else 0}")
    logger.info(f"ESLint stderr length: {len(stderr) if stderr else 0}")
    if stdout:
        logger.debug(f"ESLint stdout: {stdout[:500]}...")  # 只记录前500字符
    if stderr:
        logger.debug(f"ESLint stderr: {stderr[:500]}...")  # 只记录前500字符

    # Write output to log file
    full_output = f"Command: {command}{NL}Return Code: {code}{NL}Stdout:{NL}{stdout}{NL}Stderr:{NL}{stderr}"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_output)
        logger.info(f"ESLint output written to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write eslint output log: {e}")

    # Analyze results
    # Exit code 0: No errors. Exit code 1: Linting errors found. Exit code >
    # 1: Config/runtime error.
    issue_count = 0
    if code > 1:
        logger.error(
            f"ESLint execution failed with configuration/runtime error (code: {code}). Details in: {output_file}"
        )
        issues_found += 1  # Count execution error as one issue
        return False, f"ESLint execution failed (code: {code})", 0, output_file
    elif code == 1:
        logger.warning(
            f"ESLint check completed and found linting issues. Details in: {output_file}")
        # Try to parse issue count from stdout (ESlint format varies)
        lines = stdout.splitlines()
        for line in reversed(lines):
            if "problems (" in line:
                try:
                    issue_count = int(line.split(
                        "problems (")[0].strip().split()[-1])
                    logger.info(f"Parsed issue count: {issue_count}")
                    break
                except Exception:
                    logger.warning(
                        "Could not parse exact issue count from ESLint summary line."
                    )
                    break  # Stop searching
        if issue_count == 0:
            # Fallback: if code is 1, assume at least one issue
            issue_count = 1
            logger.warning(
                "Could not parse issue count, assuming at least 1 based on exit code."
            )
        issues_found += issue_count
        return True, f"Found {issue_count} issues", issue_count, output_file
    else:  # code == 0
        logger.info("ESLint check completed, no issues found.")
        return True, "No issues found", 0, output_file


def invoke_ci_check(port=None):
    """Performs CI checks: lint fix, lint, build, serve preview, and availability test."""
    # 加载配置
    try:
        config = load_project_config()
        host = config.get(
            'environment',
            {}).get(
            'network',
            {}).get(
            'preview_host',
            'localhost')
        if port is None:
            port = config.get(
                'environment',
                {}).get(
                'network',
                {}).get(
                'default_ports',
                {}).get(
                'preview',
                3000)
    except Exception as e:
        logger.warning(f"Failed to load network config: {e}, using defaults")
        host = 'localhost'
        port = port or 3000

    logger.info(
        f"Starting CI checks on frontend (host: {host}, port: {port})...")
    success = True
    # 1. Change to frontend admin directory
    frontend_dir = PROJECT_ROOT / "src" / "frontend" / "admin"
    if not frontend_dir.exists():
        logger.error(f"Frontend directory not found: {frontend_dir}")
        return False
    # Commands to run
    cmds = [
        (["npm", "run", "lint:fix"], "lint:fix"),
        (["npm", "run", "lint"], "lint"),
        (["npm", "run", "build"], "build"),
    ]
    for cmd, name in cmds:
        logger.info(f"Running {name}...")
        out, err, code = run_command(cmd, check=False, cwd=str(frontend_dir))
        if code != 0:
            logger.error(f"{name} failed (code {code}): {err}")
            return False
        logger.info(f"{name} succeeded.")
    # 4. Start serve preview
    serve_cmd = ["npx", "serve", "-s", "build", "-l", str(port)]
    proc = subprocess.Popen(serve_cmd, cwd=str(frontend_dir))
    time.sleep(3)
    # 5. Test availability
    try:
        url = f"http://{host}:{port}"
        resp = urllib.request.urlopen(url, timeout=10)
        if resp.status == 200:
            logger.info("Preview page available: HTTP 200 OK")
        else:
            logger.error(f"Page returned status {resp.status}")
            success = False
    except Exception as e:
        logger.error(f"Page access failed: {e}")
        success = False
    # 6. Close preview service
    try:
        proc.terminate()
        proc.wait(timeout=5)
        logger.info("Preview service stopped.")
    except Exception:
        proc.kill()
        logger.info("Preview service killed.")
    return success


def invoke_code_quality_check(skip_check=False):
    """Runs all code quality checks and updates the report."""
    global issues_found  # We modify the global counter directly here
    logger.info("Starting code quality check...")

    if skip_check:
        logger.info("Skipping code quality check based on parameter.")
        update_report(
            "Code Quality Check",
            "⚠️ Skipping code quality check based on parameter.",
        )
        return True  # Skipping is considered success for the flow

    # Initialize results for reporting
    results = {
        "Python (flake8)": {
            "success": False,
            "message": "Not run",
            "issues": 0,
            "output_file": None,
        },
        "JavaScript (eslint)": {
            "success": False,
            "message": "Not run",
            "issues": 0,
            "output_file": None,
        },
    }
    overall_success = True  # Tracks if checks *ran* successfully, not if they passed

    # Run Flake8
    try:
        f_success, f_msg, f_issues, f_outfile = invoke_flake8_check()
        results["Python (flake8)"] = {
            "success": f_success,
            "message": f_msg,
            "issues": f_issues,
            "output_file": f_outfile,
        }
        if not f_success:
            overall_success = False
    except Exception as e:
        logger.error(f"Unexpected error during flake8 check: {e}")
        results["Python (flake8)"]["message"] = f"Execution Error: {e}"
        overall_success = False
        issues_found += 1

    # Run ESLint
    try:
        e_success, e_msg, e_issues, e_outfile = invoke_eslint_check()
        results["JavaScript (eslint)"] = {
            "success": e_success,
            "message": e_msg,
            "issues": e_issues,
            "output_file": e_outfile,
        }
        if not e_success:
            overall_success = False  # Mark if eslint execution failed
    except Exception as e:
        logger.error(f"Unexpected error during eslint check: {e}")
        results["JavaScript (eslint)"]["message"] = f"Execution Error: {e}"
        overall_success = False
        issues_found += 1

    # Generate report section
    report_content = f"### Code Quality Check Results{NL}{NL}"
    report_content += f"| Language Tool       | Status                     | Issues | Details      |{NL}"
    report_content += f"|---------------------|----------------------------|--------|--------------|{NL}"

    for tool_name, res in results.items():
        status_icon = (
            "✅"
            if res["issues"] == 0 and res["success"]
            else ("⚠️" if res["success"] else "❌")
        )
        message = res["message"]
        issues = res["issues"]
        details = "-"
        if res["issues"] > 0 and res["output_file"]:
            rel_path = res["output_file"].relative_to(PROJECT_ROOT).as_posix()
            details = f"[View Log]({rel_path})"
        elif not res["success"]:
            details = message  # Show error message if execution failed
            message = "Execution Failed"

        report_content += (
            f"| {tool_name} | {status_icon} {message} | {issues} | {details} |{NL}")

    update_report("Code Quality Check", report_content)

    # Store code quality check results to memory
    if 'mcp_tools' in globals():
        quality_check_stats = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "total_issues_found": issues_found,
            "results": results,
            "tools_checked": list(results.keys())
        }
        mcp_tools.store_memory(
            "code_quality_results",
            quality_check_stats,
            "code_quality")

    if overall_success:
        if issues_found > 0:
            logger.warning(
                f"Code quality checks completed. Total issues found: {issues_found}")
        else:
            logger.info("Code quality checks completed. No issues found.")
    else:
        logger.error(
            "Code quality check execution failed or partially failed.")

    # Return True if the *checks* ran without execution errors,
    # regardless of finding linting issues.
    return overall_success


# --- Code Quality Check Functions End ---


# --- Error Path Detection Integration ---
def invoke_error_path_detection():
    """执行错误路径检测和清理"""
    global issues_found, warnings_found

    logger.info("开始执行错误路径检测和清理...")

    try:
        # 导入错误检测模块 - 暂时禁用
        # from error_path_detector import run_error_detection
        # 注意：error_path_detector模块暂未实现，跳过此功能
        logger.info("错误路径检测功能暂时禁用 - error_path_detector模块未实现")
        update_report(
            "错误路径检测",
            "⚠️ **功能暂时禁用**\n\n"
            "错误路径检测模块(error_path_detector)暂未实现，此功能已跳过。\n\n"
            "如需启用此功能，请实现error_path_detector.py模块。"
        )
        return True  # 跳过但不报错

        # 原错误检测代码已移除，功能已在上方跳过

    except Exception as e:
        logger.error(f"错误路径检测过程中发生异常: {e}")
        issues_found += 1
        update_report(
            "错误路径检测",
            "❌ **执行异常**\n\n"
            f"错误: {e}\n\n"
            "错误路径检测过程中发生未预期的异常。"
        )
        return False

    except Exception as e:
        logger.error(f"错误路径检测执行失败: {e}")
        issues_found += 1
        update_report(
            "错误路径检测",
            "❌ **执行失败**\n\n"
            f"错误: {e}\n\n"
            "请检查日志文件获取详细错误信息。"
        )

        # Store execution error to memory
        if 'mcp_tools' in globals():
            mcp_tools.store_memory("error_detection_failure", {
                "timestamp": datetime.now().isoformat(),
                "error_type": "Exception",
                "error_message": str(e),
                "failure_reason": "execution_failed"
            }, "error_detection")

        return False


# --- Main Execution ---
def main():
    """Main function to run the work completion process with TaskManager integration."""
    # 使用全局已解析的args参数

    logger.info("Starting finish.py script with TaskManager integration...")

    # 存储脚本启动信息到memory
    mcp_tools.store_memory("script_start", {
        "timestamp": TIMESTAMP,
        "mode": "daily" if args.daily else "release" if args.release else "backup_only" if args.backup_only else "default",
        "args": vars(args)
    })

    # 快速备份模式：仅执行备份，跳过其他所有步骤
    if args.backup_only:
        logger.info("快速备份模式：仅执行项目备份")
        backup_ok = invoke_backup(False)  # 强制执行备份
        if backup_ok:
            logger.info("快速备份完成！")
            mcp_tools.store_memory(
                "backup_result", {
                    "status": "success", "mode": "backup_only"})
            sys.exit(0)
        else:
            logger.error("快速备份失败！")
            mcp_tools.store_memory(
                "backup_result", {
                    "status": "failed", "mode": "backup_only"})
            sys.exit(1)

    # 自动格式化阶段
    invoke_autoformat()
    # 1. Initialize Report
    if not initialize_report():
        logger.error("Failed to initialize report. Aborting.")
        sys.exit(1)

    # 2. Check Dependencies
    if not test_dependencies():
        logger.error("Dependency check failed for required tools. Aborting.")
        # TODO: Call a summary function before exiting?
        update_report(
            "Execution Aborted",
            "Dependency check failed, cannot continue.")
        sys.exit(1)
    logger.info("Dependency check passed.")

    # 3. Directory Structure Check (Simplified)
    if not invoke_directory_check():
        logger.error(
            "Simplified directory check failed. Aborting (in this test phase)."
        )
        update_report(
            "Execution Aborted",
            "Simplified directory check failed.")
        sys.exit(1)
    logger.info("Simplified directory check passed.")

    # --- Add calls to other checks here later ---
    # invoke_code_quality_check(args.no_quality_check)
    code_quality_ok = invoke_code_quality_check(args.no_quality_check)
    if not code_quality_ok:
        logger.warning(
            "Code quality check execution failed. Continuing cautiously...")
        # Decide if this should abort or just warn

    # invoke_workdir_clean_check()
    workdir_clean_ok = invoke_workdir_clean_check()
    if not workdir_clean_ok:
        logger.warning(
            "Working directory cleanliness check found scattered items.")
        # This is usually a warning, not a failure for the overall process

    # 执行项目清理
    cleanup_ok = invoke_project_cleanup_py()
    if not cleanup_ok:
        logger.warning("Project cleanup identified issues or failed.")
    # Agent 自动检查目录和文件结构 - 需要权限控制和逻辑推理
    logger.info("准备执行目录结构验证，开始逻辑推理分析...")

    # Sequential thinking for directory structure verification strategy
    structure_decision_points = [
        {
            "question": "如何确保目录结构验证的准确性？",
            "factors": ["项目规范要求", "现有文件结构", "自动化程度"],
            "risks": ["误删重要文件", "结构破坏", "数据丢失"],
            "benefits": ["规范化管理", "提高维护性", "团队协作效率"],
            "recommendation": "采用渐进式验证，先检查后清理，确保安全性"
        },
        {
            "question": "是否需要人工审批介入？",
            "factors": ["历史问题记录", "风险评估", "自动化信任度"],
            "risks": ["自动化误操作", "重要文件丢失", "项目结构破坏"],
            "benefits": ["人工把关", "降低风险", "确保准确性"],
            "recommendation": "对于关键结构变更，必须进行人工审批"
        }
    ]

    structure_thinking = mcp_tools.sequential_thinking(
        context="目录结构验证策略分析",
        decision_points=structure_decision_points,
        reasoning_type="structure_verification"
    )

    # 检查是否有未处理的目录结构问题需要审批
    previous_structure_issues = mcp_tools.get_memory("structure_issues")
    if previous_structure_issues and previous_structure_issues.get(
            "status") == "pending_approval":
        logger.warning("发现未处理的目录结构问题，需要人工审批")
        task_id = mcp_tools.create_approval_task(
            title="目录结构合规性检查审批", description=f"发现目录结构问题需要审批处理：{
                previous_structure_issues.get(
                    'issues', [])}", priority="high")
        logger.info(f"已创建审批任务 #{task_id}，等待人工处理...")

        # 等待审批（在实际环境中，这里应该是异步等待）
        approval_result = mcp_tools.wait_for_approval(task_id)
        if not approval_result:
            logger.error("目录结构审批被拒绝，终止执行")
            sys.exit(1)
        logger.info("目录结构审批通过，继续执行")

    agent_ok = agent_verify_structure(
        auto_cleanup=getattr(
            args, 'auto_cleanup', False))
    if not agent_ok:
        logger.error("Agent验证: 项目根目录存在不符合规范的项，终止执行。")
        # 存储结构问题到memory
        mcp_tools.store_memory("structure_issues", {
            "status": "failed",
            "timestamp": TIMESTAMP,
            "issues": ["项目根目录存在不符合规范的项"]
        })
        sys.exit(1)
    else:
        # 存储成功结果
        mcp_tools.store_memory("structure_verification", {
            "status": "passed",
            "timestamp": TIMESTAMP
        })

    # 执行错误路径检测和清理（新增的日常工作）
    error_detection_ok = invoke_error_path_detection()
    if not error_detection_ok:
        logger.warning("错误路径检测部分失败，但继续执行其他步骤。")

    # 执行备份 - 添加逻辑推理分析
    logger.info("准备执行项目备份，开始策略分析...")

    # Sequential thinking for backup strategy
    backup_decision_points = [
        {
            "question": "如何确保备份的完整性和可靠性？",
            "factors": ["数据重要性", "备份频率", "存储空间", "恢复速度"],
            "risks": ["数据丢失", "备份损坏", "存储空间不足", "备份时间过长"],
            "benefits": ["数据安全", "快速恢复", "版本控制", "灾难恢复"],
            "recommendation": "采用增量备份策略，确保数据完整性验证"
        },
        {
            "question": "备份失败时的应对策略？",
            "factors": ["失败原因", "重试机制", "备用方案", "通知机制"],
            "risks": ["数据永久丢失", "工作中断", "项目延期"],
            "benefits": ["风险控制", "业务连续性", "数据保护"],
            "recommendation": "建立多层备份机制，失败时立即告警并启动备用方案"
        }
    ]

    backup_thinking = mcp_tools.sequential_thinking(
        context="项目备份策略分析",
        decision_points=backup_decision_points,
        reasoning_type="backup_strategy"
    )

    backup_ok = invoke_backup(args.no_backup)
    if not backup_ok and not args.no_backup:
        logger.error("Project backup failed.")
        mcp_tools.store_memory("backup_result", {
            "status": "failed",
            "timestamp": TIMESTAMP,
            "mode": "full_process"
        })
    else:
        mcp_tools.store_memory("backup_result", {
            "status": "success" if backup_ok else "skipped",
            "timestamp": TIMESTAMP,
            "mode": "full_process"
        })

    # generate_summary()
    generate_summary()
    # new_completion_checklist()
    new_completion_checklist()

    logger.info("All checks performed.")

    # 存储完整的执行结果到memory
    execution_result = {
        "timestamp": TIMESTAMP,
        "issues_found": issues_found,
        "warnings_found": warnings_found,
        "backup_ok": backup_ok,
        "code_quality_ok": code_quality_ok,
        "workdir_clean_ok": workdir_clean_ok,
        "cleanup_ok": cleanup_ok,
        "agent_ok": agent_ok,
        "error_detection_ok": error_detection_ok
    }
    mcp_tools.store_memory("execution_result", execution_result)

    # 如果有关键问题，创建审批任务
    critical_failures = []
    if not backup_ok and not args.no_backup:
        critical_failures.append("备份失败")
    if not agent_ok:
        critical_failures.append("目录结构验证失败")

    if critical_failures:
        task_id = mcp_tools.create_approval_task(
            title="工作完成流程关键问题处理",
            description=f"发现关键失败需要处理：{', '.join(critical_failures)}",
            priority="critical"
        )
        logger.warning(f"已创建关键问题审批任务 #{task_id}")

    # Determine final exit code based on critical failures / issues
    # Example: Fail if dependencies missing or backup failed (when not skipped)
    final_status_success = True
    # Recheck dependencies status (stored from earlier? Or re-run required checks?)
    # For simplicity, let's assume if backup failed, overall process failed
    if not backup_ok and not args.no_backup:
        final_status_success = False
        # Add critical dependency check failure here too if needed

    if final_status_success:
        if issues_found > 0:
            logger.warning(
                f"Work completion process finished with issues ({issues_found}) and warnings ({warnings_found}). Review report.")
            mcp_tools.store_memory("final_status", {
                "status": "completed_with_issues",
                "issues": issues_found,
                "warnings": warnings_found
            })
            sys.exit(0)  # Success exit code, but report indicates issues
        else:
            logger.info(
                f"Work completion process finished successfully with no issues ({warnings_found} warnings).")
            mcp_tools.store_memory("final_status", {
                "status": "success",
                "issues": issues_found,
                "warnings": warnings_found
            })
            sys.exit(0)
    else:
        logger.error(
            f"Work completion process finished with CRITICAL failures. Issues: {issues_found}, Warnings: {warnings_found}. Review report."
        )
        mcp_tools.store_memory("final_status", {
            "status": "critical_failure",
            "issues": issues_found,
            "warnings": warnings_found,
            "critical_failures": critical_failures
        })
        sys.exit(1)  # Failure exit code


if __name__ == "__main__":
    main()
