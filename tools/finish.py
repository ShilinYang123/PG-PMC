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
from datetime import datetime
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"

# 读取项目配置
def load_project_config():
    """加载项目配置文件"""
    config_file = PROJECT_ROOT / "docs" / "03-管理" / "project_config.yaml"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

# 加载配置
project_config = load_project_config()
git_config = project_config.get('git', {})
GIT_REPO_DIR = PROJECT_ROOT / "bak" / git_config.get('repo_dir_name', 'github_repo')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
            encoding='utf-8'
        )

        if result.returncode == 0:
            logger.info("目录结构检查完成")
            print(result.stdout)
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

    control_script = TOOLS_DIR / "control.py"
    if not control_script.exists():
        logger.error(f"控制脚本不存在: {control_script}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(control_script), "backup"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            logger.info("备份操作完成")
            return True
        else:
            logger.error(f"备份操作失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"执行备份时出错: {e}")
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
            text=True
        )

        if result.stdout.strip():
            # 有未提交的更改
            logger.info("发现未提交的更改，开始提交...")

            # 添加所有更改
            subprocess.run(
                ["git", "add", "."],
                cwd=str(GIT_REPO_DIR),
                check=True
            )

            # 提交更改
            commit_prefix = git_config.get('commit_message_prefix', '自动备份')
            commit_msg = f"{commit_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(GIT_REPO_DIR),
                check=True
            )

            logger.info("更改已提交")

        # 推送到远程仓库
        result = subprocess.run(
            ["git", "push"],
            cwd=str(GIT_REPO_DIR),
            capture_output=True,
            text=True
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
    print("🚀 启动项目完成流程")
    print(f"📁 项目根目录: {PROJECT_ROOT}")
    print("-" * 60)

    success_count = 0
    total_steps = 3

    # 1. 目录结构检查
    print("\n📋 步骤 1/3: 目录结构检查")
    if run_structure_check():
        success_count += 1
        print("✅ 目录结构检查完成")
    else:
        print("❌ 目录结构检查失败")

    # 2. 备份操作
    print("\n💾 步骤 2/3: 备份操作")
    if run_backup():
        success_count += 1
        print("✅ 备份操作完成")
    else:
        print("❌ 备份操作失败")

    # 3. Git推送
    print("\n🔄 步骤 3/3: Git推送")
    if run_git_push():
        success_count += 1
        print("✅ Git推送完成")
    else:
        print("❌ Git推送失败")

    # 总结
    print("\n" + "=" * 60)
    print(f"📊 完成情况: {success_count}/{total_steps} 步骤成功")

    if success_count == total_steps:
        print("🎉 所有步骤都已成功完成！")
        return 0
    else:
        print("⚠️ 部分步骤失败，请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
