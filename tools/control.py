#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件权限控制脚本 - 简化版
功能：检查核心文件状态、设置权限、自动备份
作者：雨俊
日期：2025-01-21
"""

import os
import stat
import shutil
import datetime
from pathlib import Path
import yaml

# 受保护的核心文件列表
PROTECTED_FILES = [
    "docs/01-设计/开发任务书.md",
    "docs/01-设计/技术路线.md",
    "docs/01-设计/项目架构设计.md",
    "docs/01-设计/目录结构标准清单.md",
    "docs/03-管理/规范与流程.md",
    "docs/03-管理/project_config.yaml",

    "tools/finish.py",
    "tools/control.py",
    "tools/check_structure.py",
    "tools/update_structure.py"
]


def load_project_config():
    """加载项目配置"""
    config_path = Path(__file__).parent.parent / "docs" / "03-管理" / "project_config.yaml"
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
    
    # 备用方案：向上查找包含docs目录的根目录
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:
        if (current_dir / "docs").exists():
            return current_dir
        current_dir = current_dir.parent
    return Path(__file__).parent.parent  # 默认为工具目录的上级


def is_readonly(file_path):
    """检查文件是否为只读"""
    try:
        file_stat = os.stat(file_path)
        return not (file_stat.st_mode & stat.S_IWRITE)
    except FileNotFoundError:
        return None


def set_readonly(file_path, readonly=True):
    """设置文件只读或可写"""
    try:
        current_mode = os.stat(file_path).st_mode
        if readonly:
            # 移除写权限
            new_mode = current_mode & ~stat.S_IWRITE
        else:
            # 添加写权限
            new_mode = current_mode | stat.S_IWRITE
        os.chmod(file_path, new_mode)
        return True
    except Exception as e:
        print(f"设置文件权限失败 {file_path}: {e}")
        return False


def check_files_status(project_root):
    """检查所有受保护文件的状态"""
    print("\n=== 核心文件权限状态检查 ===")
    print(f"项目根目录: {project_root}")
    print("-" * 60)

    readonly_files = []
    writable_files = []
    missing_files = []

    for file_rel_path in PROTECTED_FILES:
        file_path = project_root / file_rel_path
        status = is_readonly(file_path)

        if status is None:
            missing_files.append(file_rel_path)
            print(f"❌ 缺失: {file_rel_path}")
        elif status:
            readonly_files.append(file_rel_path)
            print(f"🔒 只读: {file_rel_path}")
        else:
            writable_files.append(file_rel_path)
            print(f"✏️  可写: {file_rel_path}")

    print("-" * 60)
    print(
        f"统计: 只读 {
            len(readonly_files)} 个, 可写 {
            len(writable_files)} 个, 缺失 {
                len(missing_files)} 个")

    return readonly_files, writable_files, missing_files


def backup_files(project_root, files_to_backup):
    """备份文件到专项备份目录"""
    config = load_project_config()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 从配置获取备份目录
    if config and config.get('paths', {}).get('backup_dir'):
        backup_base = Path(config['paths']['backup_dir'])
    else:
        backup_base = project_root / "bak"
    
    backup_dir = backup_base / "专项备份" / f"权限变更备份_{timestamp}"

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up_files = []
        for file_rel_path in files_to_backup:
            source_file = project_root / file_rel_path
            if source_file.exists():
                # 保持目录结构
                backup_file = backup_dir / file_rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, backup_file)
                backed_up_files.append(file_rel_path)

        print(f"\n✅ 备份完成: {backup_dir}")
        print(f"已备份 {len(backed_up_files)} 个文件:")
        for file_path in backed_up_files:
            print(f"  - {file_path}")

        return True, backup_dir
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        return False, None


def set_files_permission(project_root, files, readonly=True):
    """批量设置文件权限"""
    action = "只读" if readonly else "可写"
    print(f"\n正在设置文件为{action}状态...")

    success_files = []
    failed_files = []

    for file_rel_path in files:
        file_path = project_root / file_rel_path
        if file_path.exists():
            if set_readonly(file_path, readonly):
                success_files.append(file_rel_path)
                print(f"✅ {file_rel_path} -> {action}")
            else:
                failed_files.append(file_rel_path)
                print(f"❌ {file_rel_path} -> 设置失败")
        else:
            failed_files.append(file_rel_path)
            print(f"❌ {file_rel_path} -> 文件不存在")

    print(f"\n权限设置完成: 成功 {len(success_files)} 个, 失败 {len(failed_files)} 个")
    return success_files, failed_files


def main():
    """主函数"""
    print("文件权限控制工具 - 简化版")
    print("=" * 40)

    project_root = get_project_root()

    # 1. 检查当前文件状态
    readonly_files, writable_files, missing_files = check_files_status(
        project_root)

    if missing_files:
        print(f"\n⚠️  警告: 发现 {len(missing_files)} 个文件缺失，请检查项目完整性")

    # 2. 询问用户操作
    print("\n请选择操作:")
    print("1. 设置所有文件为只读")
    print("2. 设置所有文件为可写")
    print("按 0 退出")

    while True:
        try:
            choice = input("\n请输入选择 (1-2, 0退出): ").strip()
        except KeyboardInterrupt:
            print("\n\n用户中断操作，退出程序")
            return
        except EOFError:
            print("\n\n输入结束，退出程序")
            return

        if choice == "0":
            print("退出程序")
            return

        elif choice in ["1", "2"]:
            readonly_mode = (choice == "1")
            action = "只读" if readonly_mode else "可写"

            # 确认操作
            confirm = input(
                f"确认要将所有核心文件设置为{action}状态吗? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("操作已取消")
                continue

            # 3. 如果设为可写，先备份
            if not readonly_mode:
                print("\n正在备份文件...")
                existing_files = [
                    f for f in PROTECTED_FILES if (
                        project_root / f).exists()]
                backup_success, backup_dir = backup_files(
                    project_root, existing_files)
                if not backup_success:
                    print("备份失败，操作已取消")
                    continue

            # 设置权限
            existing_files = [
                f for f in PROTECTED_FILES if (
                    project_root / f).exists()]
            success_files, failed_files = set_files_permission(
                project_root, existing_files, readonly_mode)

            if failed_files:
                print(f"\n⚠️  部分文件权限设置失败，请检查文件是否被占用")
            else:
                print(f"\n🎉 所有文件已成功设置为{action}状态")

            break
        else:
            print("无效选择，请输入 1-2 或 0")


if __name__ == "__main__":
    main()
