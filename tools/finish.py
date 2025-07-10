#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目完成脚本 - 简化版

核心功能：
1. 调用check_structure.py进行目录结构检查
2. 执行备份操作
3. Git推送

作者：雨俊
创建时间：2025-07-08
"""


import sys
import subprocess
import logging
import yaml
import shutil
from datetime import datetime
from pathlib import Path

# Windows平台下设置控制台编码为UTF-8
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"


# 读取项目配置
def load_project_config():
    """加载项目配置文件"""
    config_file = PROJECT_ROOT / "docs" / "03-管理" / "project_config.yaml"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


# 加载配置
project_config = load_project_config()
git_config = project_config.get("git", {})
GIT_REPO_DIR = PROJECT_ROOT / "bak" / git_config.get("repo_dir_name", "github_repo")

# 使用统一的日志配置
sys.path.insert(0, str(TOOLS_DIR))
from logging_config import get_logger

logger = get_logger("finish")


def run_structure_check():
    """运行目录结构检查"""
    logger.info("开始目录结构检查...")

    check_script = TOOLS_DIR / "check_structure.py"
    if not check_script.exists():
        logger.error(f"检查脚本不存在: {check_script}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(check_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode == 0:
            logger.info("目录结构检查完成")
            return True
        else:
            logger.error(f"目录结构检查失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"运行目录结构检查时出错: {e}")
        return False


def run_backup():
    """执行备份操作"""
    logger.info("开始备份操作...")

    try:
        # 创建备份目录
        backup_base_dir = PROJECT_ROOT / "bak" / "专项备份"
        backup_base_dir.mkdir(parents=True, exist_ok=True)

        # 生成备份目录名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_base_dir / f"自动备份_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

        # 定义需要备份的核心文件
        core_files = [
            "docs/01-设计/开发任务书.md",
            "docs/01-设计/技术方案.md",
            "docs/01-设计/项目架构设计.md",
            "docs/01-设计/目录结构标准清单.md",
            "docs/03-管理/规范与流程.md",
            "docs/03-管理/project_config.yaml",
            "tools/finish.py",
            "tools/control.py",
            "tools/check_structure.py",
            "tools/update_structure.py",
        ]

        backup_count = 0
        for file_path in core_files:
            source_file = PROJECT_ROOT / file_path
            if source_file.exists():
                # 创建目标目录
                target_file = backup_dir / file_path
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(source_file, target_file)
                backup_count += 1

        logger.info(f"备份操作完成，已备份 {backup_count} 个文件到: {backup_dir}")
        return True

    except Exception as e:
        logger.error(f"执行备份时出错: {e}")
        return False


def run_pre_commit_check():
    """运行Git提交前检查"""
    logger.info("开始Git提交前检查...")

    check_script = GIT_REPO_DIR / "tools" / "git_pre_commit_check.py"
    if not check_script.exists():
        logger.warning(f"提交前检查脚本不存在: {check_script}")
        return True  # 如果脚本不存在，允许继续

    try:
        result = subprocess.run(
            [sys.executable, str(check_script)],
            cwd=str(GIT_REPO_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",  # 忽略编码错误
        )

        if result.returncode == 0:
            logger.info("Git提交前检查通过")
            return True
        else:
            logger.error(f"Git提交前检查失败: {result.stderr}")
            print(result.stdout)  # 显示检查结果
            return False

    except Exception as e:
        logger.error(f"运行Git提交前检查时出错: {e}")
        return False


def run_git_push():
    """执行Git推送"""
    logger.info("开始Git推送...")

    # 检查git仓库目录是否存在
    if not GIT_REPO_DIR.exists():
        logger.error(f"Git仓库目录不存在: {GIT_REPO_DIR}")
        return False

    # 检查是否为git仓库
    if not (GIT_REPO_DIR / ".git").exists():
        logger.error(f"目录不是Git仓库: {GIT_REPO_DIR}")
        return False

    try:
        # 检查Git状态
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(GIT_REPO_DIR),
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
        )

        if result.stdout.strip():
            # 有未提交的更改
            logger.info("发现未提交的更改，开始提交...")

            # 添加所有更改
            subprocess.run(
                ["git", "add", "."],
                cwd=str(GIT_REPO_DIR),
                capture_output=True,
                text=True,
                encoding="gbk",
                errors="ignore",
                check=True,
            )

            # 运行提交前检查
            logger.info("执行提交前检查...")
            if not run_pre_commit_check():
                logger.error("提交前检查失败，取消提交")
                return False

            # 提交更改
            commit_prefix = git_config.get("commit_message_prefix", "自动备份")
            commit_msg = (
                f"{commit_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(GIT_REPO_DIR),
                capture_output=True,
                text=True,
                encoding="gbk",
                errors="ignore",
                check=True,
            )

            logger.info("更改已提交")

        # 推送到远程仓库
        result = subprocess.run(
            ["git", "push"],
            cwd=str(GIT_REPO_DIR),
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
        )

        if result.returncode == 0:
            logger.info("Git推送完成")
            return True
        else:
            logger.error(f"Git推送失败: {result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Git操作失败: {e}")
        return False
    except Exception as e:
        logger.error(f"执行Git推送时出错: {e}")
        return False


def main():
    """主函数"""
    try:
        print("[START] 启动项目完成流程")
        print(f"[INFO] 项目根目录: {PROJECT_ROOT}")
        print("-" * 60)

        success_count = 0
        total_steps = 3
        print(f"[DEBUG] 初始化完成，准备执行 {total_steps} 个步骤")

        # 1. 目录结构检查
        print("\n[STEP 1/3] 目录结构检查")
        check_result = run_structure_check()
        print(f"[DEBUG] 目录结构检查返回值: {check_result}")
        if check_result:
            success_count += 1
            print("[SUCCESS] 目录结构检查完成")
        else:
            print("[FAILED] 目录结构检查失败")

        # 2. 备份操作
        print("\n[STEP 2/3] 备份操作")
        backup_result = run_backup()
        print(f"[DEBUG] 备份操作返回值: {backup_result}")
        if backup_result:
            success_count += 1
            print("[SUCCESS] 备份操作完成")
        else:
            print("[FAILED] 备份操作失败")

        # 3. Git推送
        print("\n[STEP 3/3] Git推送")
        if run_git_push():
            success_count += 1
            print("[SUCCESS] Git推送完成")
        else:
            print("[FAILED] Git推送失败")

        # 总结
        print("\n" + "=" * 60)
        print(f"[SUMMARY] 完成情况: {success_count}/{total_steps} 步骤成功")

        if success_count == total_steps:
            print("[COMPLETE] 所有步骤都已成功完成！")
            return 0
        else:
            print("[WARNING] 部分步骤失败，请检查日志")
            return 1

    except Exception as e:
        print(f"[ERROR] 执行过程中发生异常: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
