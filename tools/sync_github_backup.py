#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub备份同步验证脚本

功能：
1. 检查GitHub备份仓库名称是否与当前项目匹配
2. 确保备份的是当前项目最新的三大目录（docs、project、tools）
3. 提供同步功能

作者：雨俊
创建时间：2025-07-10
"""

import sys
import os
import shutil
import subprocess
import yaml
from pathlib import Path
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"

# 添加tools目录到Python路径
sys.path.insert(0, str(TOOLS_DIR))
from logging_config import get_logger

logger = get_logger("sync_github_backup")

def load_project_config():
    """加载项目配置文件"""
    config_file = PROJECT_ROOT / "docs" / "03-管理" / "project_config.yaml"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

def get_git_repo_info(repo_path):
    """获取Git仓库信息"""
    try:
        # 获取远程仓库URL
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'origin' in line and '(fetch)' in line:
                    url = line.split()[1]
                    return url
        return None
    except Exception as e:
        logger.error(f"获取Git仓库信息失败: {e}")
        return None

def check_repo_name_match(repo_url, project_name):
    """检查仓库名称是否与项目名称匹配"""
    if not repo_url:
        return False
    
    # 从URL中提取仓库名
    if repo_url.endswith('.git'):
        repo_name = repo_url.split('/')[-1][:-4]  # 移除.git后缀
    else:
        repo_name = repo_url.split('/')[-1]
    
    logger.info(f"GitHub仓库名: {repo_name}")
    logger.info(f"项目名称: {project_name}")
    
    return repo_name.lower() == project_name.lower()

def compare_directories(source_dir, target_dir):
    """比较两个目录的差异"""
    differences = []
    
    if not source_dir.exists():
        differences.append(f"源目录不存在: {source_dir}")
        return differences
    
    if not target_dir.exists():
        differences.append(f"目标目录不存在: {target_dir}")
        return differences
    
    # 比较文件和子目录
    source_items = set(item.name for item in source_dir.rglob('*') if item.is_file())
    target_items = set(item.name for item in target_dir.rglob('*') if item.is_file())
    
    only_in_source = source_items - target_items
    only_in_target = target_items - source_items
    
    if only_in_source:
        differences.append(f"仅在源目录中存在的文件: {list(only_in_source)}")
    
    if only_in_target:
        differences.append(f"仅在目标目录中存在的文件: {list(only_in_target)}")
    
    return differences

def sync_directory(source_dir, target_dir, dry_run=False):
    """同步目录"""
    logger.info(f"同步目录: {source_dir} -> {target_dir}")
    
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return False
    
    try:
        if not dry_run:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir)
            logger.info(f"目录同步完成: {target_dir}")
        else:
            logger.info(f"[模拟] 将同步目录: {source_dir} -> {target_dir}")
        return True
    except Exception as e:
        logger.error(f"同步目录失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 GitHub备份同步验证脚本")
    print(f"📁 项目根目录: {PROJECT_ROOT}")
    print("-" * 60)
    
    # 加载项目配置
    config = load_project_config()
    project_name = config.get('project_name', 'PG-Dev')
    git_config = config.get('git', {})
    repo_dir_name = git_config.get('repo_dir_name', 'github_repo')
    
    # GitHub备份仓库路径
    backup_repo_path = PROJECT_ROOT / "bak" / repo_dir_name
    
    print(f"📋 项目名称: {project_name}")
    print(f"📂 备份仓库路径: {backup_repo_path}")
    
    # 检查备份仓库是否存在
    if not backup_repo_path.exists():
        logger.error(f"GitHub备份仓库目录不存在: {backup_repo_path}")
        return 1
    
    # 检查是否为Git仓库
    if not (backup_repo_path / ".git").exists():
        logger.error(f"备份目录不是Git仓库: {backup_repo_path}")
        return 1
    
    # 获取仓库信息
    repo_url = get_git_repo_info(backup_repo_path)
    if not repo_url:
        logger.error("无法获取Git仓库URL")
        return 1
    
    print(f"🔗 GitHub仓库URL: {repo_url}")
    
    # 检查仓库名称是否匹配
    if check_repo_name_match(repo_url, project_name):
        print("✅ GitHub仓库名称与项目名称匹配")
    else:
        print("⚠️  GitHub仓库名称与项目名称不匹配")
    
    # 检查三大目录
    main_dirs = ['docs', 'project', 'tools']
    all_synced = True
    
    print("\n📊 检查三大目录同步状态:")
    for dir_name in main_dirs:
        source_dir = PROJECT_ROOT / dir_name
        target_dir = backup_repo_path / dir_name
        
        print(f"\n📁 检查目录: {dir_name}")
        
        differences = compare_directories(source_dir, target_dir)
        if differences:
            print(f"❌ 发现差异:")
            for diff in differences:
                print(f"   - {diff}")
            all_synced = False
            
            # 询问是否同步
            response = input(f"是否同步 {dir_name} 目录? (y/n): ").lower().strip()
            if response == 'y':
                if sync_directory(source_dir, target_dir):
                    print(f"✅ {dir_name} 目录同步完成")
                else:
                    print(f"❌ {dir_name} 目录同步失败")
                    all_synced = False
        else:
            print(f"✅ {dir_name} 目录已同步")
    
    if all_synced:
        print("\n🎉 所有目录都已同步")
    else:
        print("\n⚠️  部分目录需要同步")
    
    # 检查Git状态
    print("\n🔄 检查Git状态...")
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=backup_repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("📝 发现未提交的更改:")
                print(result.stdout)
                
                response = input("是否提交更改? (y/n): ").lower().strip()
                if response == 'y':
                    # 添加所有更改
                    subprocess.run(["git", "add", "."], cwd=backup_repo_path)
                    
                    # 提交更改
                    commit_msg = f"自动同步_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    subprocess.run(["git", "commit", "-m", commit_msg], cwd=backup_repo_path)
                    
                    print("✅ 更改已提交")
            else:
                print("✅ 没有未提交的更改")
    except Exception as e:
        logger.error(f"检查Git状态失败: {e}")
    
    print("\n🏁 GitHub备份同步验证完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())