#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目根目录规范防护脚本

功能：
1. 监控项目根目录，防止创建不规范的文件和目录
2. 提供清理建议和自动迁移功能
3. 集成到开发流程中，确保项目结构规范

使用方法：
    python tools/prevent_root_violations.py --check     # 检查当前状态
    python tools/prevent_root_violations.py --clean     # 清理不规范项
    python tools/prevent_root_violations.py --monitor   # 持续监控模式

作者：雨俊
版本：1.0
更新：2025-06-21
"""

from config_loader import get_config
import os
import sys
import time
import shutil
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import argparse
import json

# 导入配置加载器
sys.path.append(str(Path(__file__).parent))

# 加载配置
CONFIG = get_config()
PROJECT_ROOT = CONFIG['project_root']


class RootDirectoryGuard:
    """项目根目录规范防护器"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = Path(project_root).resolve()
        self.config = CONFIG.get(
            'structure_check', {}).get(
            'root_directory_rules', {})
        self.allowed_directories = set(
            self.config.get('allowed_directories', []))
        self.forbidden_dir_patterns = self.config.get(
            'forbidden_directory_patterns', [])
        self.forbidden_file_patterns = self.config.get(
            'forbidden_file_patterns', [])

        # 迁移目标映射
        self.migration_targets = {
            'config': 'docs/03-管理',
            'examples': 'docs/04-模板/代码示例库',
            'samples': 'docs/04-模板/代码示例库',
            'temp': 'bak/临时文件',
            'tmp': 'bak/临时文件',
            'cache': 'bak/缓存文件',
            'test': 'project/tests'
        }

        self.violations_log = []

    def scan_root_directory(self) -> Dict[str, List[str]]:
        """扫描根目录，识别违规项"""
        violations = {
            'forbidden_directories': [],
            'forbidden_files': [],
            'non_standard_directories': [],
            'non_standard_files': []
        }

        try:
            for item in self.project_root.iterdir():
                item_name = item.name

                if item.is_dir():
                    if item_name not in self.allowed_directories:
                        # 检查是否匹配禁止模式
                        is_forbidden = False
                        for pattern in self.forbidden_dir_patterns:
                            if fnmatch.fnmatch(
                                    item_name.lower(), pattern.lower()):
                                violations['forbidden_directories'].append(
                                    item_name)
                                is_forbidden = True
                                break

                        if not is_forbidden:
                            violations['non_standard_directories'].append(
                                item_name)

                elif item.is_file():
                    # 检查文件是否匹配禁止模式
                    is_forbidden = False
                    for pattern in self.forbidden_file_patterns:
                        if fnmatch.fnmatch(item_name.lower(), pattern.lower()):
                            violations['forbidden_files'].append(item_name)
                            is_forbidden = True
                            break

                    if not is_forbidden:
                        # 检查是否为允许的根目录文件
                        if item_name.lower() not in [
                                'readme.md', 'readme.txt', '.gitignore', 'license']:
                            violations['non_standard_files'].append(item_name)

        except Exception as e:
            print(f"❌ 扫描根目录时发生错误: {e}")

        return violations

    def suggest_migration(self, item_name: str, item_type: str) -> str:
        """建议迁移目标"""
        if item_type == 'directory':
            # 检查是否有预定义的迁移目标
            for pattern, target in self.migration_targets.items():
                if pattern in item_name.lower():
                    return target

            # 默认建议
            if 'doc' in item_name.lower():
                return 'docs/04-模板'
            elif any(word in item_name.lower() for word in ['script', 'tool', 'util']):
                return 'tools'
            else:
                return 'bak/待整理'

        else:  # file
            if item_name.lower().endswith(('.md', '.txt', '.doc', '.docx')):
                return 'docs/04-模板'
            elif item_name.lower().endswith(('.py', '.js', '.sh', '.bat')):
                return 'tools'
            elif item_name.lower().endswith(('.json', '.yaml', '.yml', '.ini', '.conf')):
                return 'docs/03-管理'
            else:
                return 'bak/待整理'

    def create_migration_plan(
            self, violations: Dict[str, List[str]]) -> List[Dict]:
        """创建迁移计划"""
        migration_plan = []

        # 处理禁止的目录
        for dir_name in violations['forbidden_directories']:
            target = self.suggest_migration(dir_name, 'directory')
            migration_plan.append({
                'type': 'directory',
                'source': dir_name,
                'target': target,
                'action': 'move',
                'reason': '匹配禁止目录模式'
            })

        # 处理非标准目录
        for dir_name in violations['non_standard_directories']:
            target = self.suggest_migration(dir_name, 'directory')
            migration_plan.append({
                'type': 'directory',
                'source': dir_name,
                'target': target,
                'action': 'move',
                'reason': '不在标准目录列表中'
            })

        # 处理禁止的文件
        for file_name in violations['forbidden_files']:
            migration_plan.append({
                'type': 'file',
                'source': file_name,
                'target': 'bak/待清理',
                'action': 'move',
                'reason': '匹配禁止文件模式'
            })

        # 处理非标准文件
        for file_name in violations['non_standard_files']:
            target = self.suggest_migration(file_name, 'file')
            migration_plan.append({
                'type': 'file',
                'source': file_name,
                'target': target,
                'action': 'move',
                'reason': '不符合根目录文件规范'
            })

        return migration_plan

    def execute_migration(
            self,
            migration_plan: List[Dict],
            dry_run: bool = True) -> bool:
        """执行迁移计划"""
        if not migration_plan:
            print("✅ 无需迁移，根目录已符合规范")
            return True

        print(f"📋 迁移计划包含 {len(migration_plan)} 项操作")

        if dry_run:
            print("\n🔍 预览模式 - 以下是将要执行的操作：")
            for i, item in enumerate(migration_plan, 1):
                print(
                    f"  {i}. {
                        item['action'].upper()} {
                        item['type']}: {
                        item['source']} -> {
                        item['target']}")
                print(f"     原因: {item['reason']}")
            print("\n💡 使用 --execute 参数实际执行迁移")
            return True

        print("\n🚀 开始执行迁移...")
        success_count = 0

        for i, item in enumerate(migration_plan, 1):
            try:
                source_path = self.project_root / item['source']
                target_dir = self.project_root / item['target']
                target_path = target_dir / item['source']

                print(
                    f"  {i}/{len(migration_plan)} 迁移 {item['source']} -> {item['target']}")

                # 确保目标目录存在
                target_dir.mkdir(parents=True, exist_ok=True)

                # 执行迁移
                if source_path.exists():
                    if target_path.exists():
                        print(f"    ⚠️ 目标已存在，跳过: {target_path}")
                        continue

                    shutil.move(str(source_path), str(target_path))
                    print(f"    ✅ 成功迁移: {item['source']}")
                    success_count += 1

                    # 记录迁移日志
                    self.violations_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'migrate',
                        'source': item['source'],
                        'target': item['target'],
                        'reason': item['reason']
                    })
                else:
                    print(f"    ❌ 源文件不存在: {source_path}")

            except Exception as e:
                print(f"    ❌ 迁移失败: {e}")

        print(f"\n📊 迁移完成: {success_count}/{len(migration_plan)} 项成功")
        return success_count == len(migration_plan)

    def save_violations_log(self):
        """保存违规日志"""
        if not self.violations_log:
            return

        log_dir = self.project_root / 'logs' / '其他日志'
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / \
            f'root_violations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.violations_log, f, ensure_ascii=False, indent=2)

        print(f"📝 违规日志已保存: {log_file}")

    def check_and_report(self) -> bool:
        """检查并报告根目录状态"""
        print("🔍 检查项目根目录规范合规性...")
        print(f"📁 项目根目录: {self.project_root}")
        print(f"✅ 允许的目录: {', '.join(self.allowed_directories)}")

        violations = self.scan_root_directory()

        total_violations = sum(len(v) for v in violations.values())

        if total_violations == 0:
            print("\n✅ 根目录规范检查通过，无违规项")
            return True

        print(f"\n❌ 发现 {total_violations} 个违规项：")

        if violations['forbidden_directories']:
            print(
                f"  🚫 禁止目录 ({
                    len(
                        violations['forbidden_directories'])}): {
                    ', '.join(
                        violations['forbidden_directories'])}")

        if violations['forbidden_files']:
            print(
                f"  🚫 禁止文件 ({
                    len(
                        violations['forbidden_files'])}): {
                    ', '.join(
                        violations['forbidden_files'])}")

        if violations['non_standard_directories']:
            print(
                f"  📁 非标准目录 ({
                    len(
                        violations['non_standard_directories'])}): {
                    ', '.join(
                        violations['non_standard_directories'])}")

        if violations['non_standard_files']:
            print(
                f"  📄 非标准文件 ({
                    len(
                        violations['non_standard_files'])}): {
                    ', '.join(
                        violations['non_standard_files'])}")

        # 生成迁移建议
        migration_plan = self.create_migration_plan(violations)
        if migration_plan:
            print("\n💡 建议的迁移方案：")
            for item in migration_plan:
                print(
                    f"  • {item['source']} -> {item['target']} ({item['reason']})")

        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="项目根目录规范防护工具")
    parser.add_argument('--check', action='store_true', help='检查当前根目录状态')
    parser.add_argument('--clean', action='store_true', help='清理不规范项（预览模式）')
    parser.add_argument('--execute', action='store_true', help='实际执行清理操作')
    parser.add_argument('--project-root', type=str, help='指定项目根目录路径')

    args = parser.parse_args()

    # 确定项目根目录
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = PROJECT_ROOT

    if not project_root.exists():
        print(f"❌ 项目根目录不存在: {project_root}")
        sys.exit(1)

    guard = RootDirectoryGuard(project_root)

    try:
        if args.check or (not args.clean and not args.execute):
            # 默认执行检查
            success = guard.check_and_report()
            sys.exit(0 if success else 1)

        elif args.clean or args.execute:
            # 执行清理
            violations = guard.scan_root_directory()
            migration_plan = guard.create_migration_plan(violations)

            if not migration_plan:
                print("✅ 根目录已符合规范，无需清理")
                sys.exit(0)

            success = guard.execute_migration(
                migration_plan, dry_run=not args.execute)

            if args.execute:
                guard.save_violations_log()

            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ 操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
