#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3AI工作室目录结构检查工具

功能：
1. 检查项目目录结构是否符合标准
2. 验证必备文件是否存在
3. 检查文件命名规范
4. 识别禁止的目录和文件
5. 生成详细的检查报告

使用方法：
    python tools/structure_check.py
    python tools/structure_check.py --verbose  # 详细输出
    python tools/structure_check.py --output logs/  # 指定输出目录

作者：雨俊
版本：2.0
更新：2025-06-13
"""

from pathlib import Path
import os
import re
from datetime import datetime
import json
from typing import Union, List, Set, Dict, Optional
import sys
import fnmatch

# 导入配置加载器
from config_loader import get_config

# 加载配置
CONFIG = get_config()
PROJECT_ROOT = CONFIG['project_root']


def parse_structure_standard() -> Dict:
    """从目录结构标准清单文件中解析检查标准"""
    # 从配置文件中读取标准清单文件路径
    standard_list_file = CONFIG.get(
        'structure_check',
        {}).get(
        'standard_list_file',
        'docs/01-设计/目录结构标准清单.md')
    md_file_path = PROJECT_ROOT / standard_list_file
    print(f"📋 从配置文件加载标准清单文件路径: {md_file_path}")
    if not md_file_path.exists():
        print(f"⚠️ 标准文件不存在: {md_file_path}")
        return get_fallback_structure()

    try:
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析Markdown文件内容以提取检查标准
        parsed_structure = {
            "required_dirs": [],
            "required_files": {},
            "template_files": {},
            "forbidden_patterns": [],
            "naming_rules": {
                "docs": r"^[\u4e00-\u9fa5a-zA-Z0-9\-_\s]+\.(md|txt)$",
                "tools": r"^[a-zA-Z0-9\-_]+\.(py|js|sh|bat|ps1)$",
                "config": r"^[a-zA-Z0-9\-_]+\.(json|yaml|yml|ini|conf)$",
            }
        }

        # 解析必需目录
        required_dirs_match = re.search(
            r"### 1\.1 核心目录\s*```\s*([^`]+)```", content, re.DOTALL)
        if required_dirs_match:
            dirs_text = required_dirs_match.group(1).strip()
            parsed_structure["required_dirs"] = [d.strip() for d in dirs_text.split(
                '\n') if d.strip() and not d.strip().startswith('#')]

        # 解析项目文件清单 (替代旧的 required_files 和 template_files)
        project_files_match = re.search(
            r"## 2\. 项目文件清单\s*```markdown\s*([^`]+)```", content, re.DOTALL)
        if project_files_match:
            files_text = project_files_match.group(1).strip()
            current_dir = ""  # 用于记录当前的目录上下文
            # 正则表达式匹配 '### 2.目录路径' 或 '### 2.目录路径/'
            dir_pattern = re.compile(
                r"^###\s*\d+(\.\d+)*\s*([^\s(]+?)/?$")  # 匹配目录行
            # 正则表达式匹配 '- `文件路径` (描述)'
            file_item_pattern = re.compile(
                r"^-\s*`([^`]+)`\s*\(([^)]+)\)$")  # 匹配文件行

            for line in files_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                dir_match = dir_pattern.match(line)
                if dir_match:
                    # current_dir = dir_match.group(2).strip() # 获取捕获组2作为目录路径
                    # 修正：目录行本身不直接用于拼接，而是作为文件行路径的前缀参考
                    # 从 '### 2.bak/.git' 或 '### 2.bak/.git/' 中提取 'bak/.git'
                    raw_dir_path = dir_match.group(2).strip()
                    if raw_dir_path.endswith('/'):
                        current_dir = raw_dir_path[:-1]
                    else:
                        current_dir = raw_dir_path
                    continue  # 处理完目录行后，继续下一行

                file_match = file_item_pattern.match(line)
                if file_match:  # 不再严格要求 current_dir，因为文件路径本身是完整的
                    # 提取文件路径，例如 'bak/.git/HEAD'
                    file_path = file_match.group(1).strip()
                    description = file_match.group(2).strip()  # 提取描述

                    # 移除路径开头的 './' 或 '.\'
                    if file_path.startswith('./'):
                        file_path = file_path[2:]
                    elif file_path.startswith('.\\'):  # Windows路径
                        file_path = file_path[2:]

                    parsed_structure["required_files"][file_path] = description

        # 解析禁止创建的目录/文件
        forbidden_patterns_match = re.search(
            r"### 3\.1 禁止创建的目录/文件类型\s*```\s*([^`]+)```", content, re.DOTALL)
        if forbidden_patterns_match:
            patterns_text = forbidden_patterns_match.group(1).strip()
            parsed_structure["forbidden_patterns"] = [p.strip() for p in patterns_text.split(
                '\n') if p.strip() and not p.strip().startswith('#')]

        # 解析文件命名规范 (如果标准文档中有定义，则覆盖默认值)
        docs_naming_match = re.search(
            r"### 4\.1 文档文件\s*.*?格式：`([^`]+)`", content, re.DOTALL)
        if docs_naming_match:
            # 从 "格式：`功能描述.md`" 中提取 `功能描述.md` 这部分作为规则的基础
            # 我们需要一个更通用的正则表达式来匹配文件名，而不是描述性文本
            # 假设标准文档中的示例代表了允许的模式，例如 .md
            # 这里我们简化处理，如果找到匹配就用一个较宽松的规则，实际应用中可能需要更精确的规则提取
            # 或者，标准文档直接提供正则表达式
            # 基于示例 `功能描述.md`，我们允许中文、英文、数字、空格、下划线、连字符，且以 .md 结尾
            # 对于 docs 目录下的 .json 和 .env 文件，我们需要更灵活的规则
            # 暂时使用一个比较通用的规则，允许字母数字和一些特殊字符，以及常见的文档和配置文件扩展名
            # 将 + 修改为 * 以允许空的文件名主体 (例如 .env)
            parsed_structure["naming_rules"][
                "docs"] = r"^[\u4e00-\u9fa5a-zA-Z0-9\-_\s\.]*\.(md|txt|json|env|example)$"

        tools_naming_match = re.search(
            r"### 4\.2 代码文件\s*.*?格式：`([^`]+)`", content, re.DOTALL)
        if tools_naming_match:
            # 示例：`module_name.py`
            parsed_structure["naming_rules"][
                "tools"] = r"^[a-zA-Z0-9_\-]+\.(py|js|sh|bat|ps1)$"

        config_naming_match = re.search(
            r"### 4\.3 配置文件\s*.*?格式：`([^`]+)`", content, re.DOTALL)
        if config_naming_match:
            # 示例：`config.json`
            parsed_structure["naming_rules"][
                "config"] = r"^[a-zA-Z0-9\._\-]+\.(json|yaml|yml|ini|conf|js|cfg|rc)$"

        print("📋 已从目录结构标准清单.md动态解析检查标准")
        return parsed_structure

    except Exception as e:
        print(f"❌ 解析标准文件失败: {e}")
        return get_fallback_structure()


def get_fallback_structure() -> Dict:
    """获取备用的硬编码结构标准（更新为新的标准化结构）"""
    return {
        "required_dirs": [
            # GitHub仓库结构规范的三个主要文件夹
            "docs",
            "project",
            "tools",
            # 本地项目结构
            "docs/01-设计",
            "docs/02-开发",
            "docs/03-管理",
            "docs/04-接口",
            "docs/05-用户",
            "docs/04-模板",
            "logs",
            "bak",
        ],
        "optional_dirs": [".devcontainer", ".github", ".vscode", "config", "scripts"],
        "required_files": {
            "docs/01-项目规划/项目目标定义.md": "项目核心目标定义",
            "docs/01-项目规划/需求分析.md": "需求分析文档",
            "docs/01-项目规划/专业项目开发框架分析报告.md": "专业框架分析",
            "docs/01-项目规划/项目实施行动计划.md": "实施行动计划",
            "docs/02-技术设计/系统架构设计.md": "系统架构设计",
            "docs/03-开发指南/开发环境搭建.md": "开发环境配置指南（合并版）",
            "docs/04-API文档/API设计规范.md": "API设计规范",
            "docs/06-项目管理/工作完成检查清单.md": "工作检查清单",
            "docs/06-项目管理/问题解决记录.md": "问题记录",
            "docs/06-项目管理/开发日志.md": "开发日志",
        },
        "template_files": {
            "docs/07-模板文件/任务书标准模板.md": "任务书模板",
            "docs/07-模板文件/检查清单标准模板.md": "检查清单模板",
            "docs/07-模板文件/问题记录标准模板.md": "问题记录模板",
        },
        "forbidden_patterns": [
            r".*[Tt]emp.*",
            r".*[Tt]mp.*",
            r".*[Bb]ackup.*",
            r".*[Oo]ld.*",
            r".*[Cc]ache.*",
            r".*\.log$",
            r".*\.tmp$",
            r".*~$",
        ],
        "naming_rules": {
            "docs": r"^[\u4e00-\u9fa5a-zA-Z0-9\-_\s]+\.(md|txt)$",
            "tools": r"^[a-zA-Z0-9\-_]+\.(py|js|sh|bat|ps1)$",
            "config": r"^[a-zA-Z0-9\-_]+\.(json|yaml|yml|ini|conf)$",
        },
    }


class StructureChecker:
    """目录结构检查器"""

    def __init__(self, project_root: Union[str, Path] = PROJECT_ROOT):
        self.project_root = Path(project_root).resolve()
        self.standard_structure = parse_structure_standard()  # 使用配置中的路径
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.missing_items: List[str] = []  # 预期但实际不存在的
        self.redundant_items: Set[str] = set()  # 实际存在但不在预期中的，改为set去重

        # 从配置文件中读取排除目录
        self.excluded_dirs_for_redundancy_check: Set[str] = set(
            CONFIG.get(
                'structure_check', {}).get(
                'excluded_dirs_for_redundancy', [
                    'bak', 'logs']))
        self.info.append(
            f"📋 从配置文件加载排除目录: {
                ', '.join(
                    self.excluded_dirs_for_redundancy_check)}")

        # 获取白名单路径时转换为小写
        raw_required_dirs = self.standard_structure.get("required_dirs", [])
        raw_required_files_map = self.standard_structure.get(
            "required_files", {})

        self.whitelist_dirs_str_lower = set(
            d.lower() for d in raw_required_dirs)
        # 对于 required_files，键（路径）转小写，值（描述）保持不变
        self.required_files_map_lower_keys = {
            k.lower(): v for k, v in raw_required_files_map.items()}
        self.whitelist_files_str_lower = set(
            self.required_files_map_lower_keys.keys())

        # 将小写相对路径字符串转换为 Path 对象，以便于比较
        self.whitelist_dirs_pathobj = {
            Path(p) for p in self.whitelist_dirs_str_lower}
        self.whitelist_files_pathobj = {
            Path(p) for p in self.whitelist_files_str_lower}

        if self.standard_structure.get("required_dirs"):  # 检查是否成功解析
            print("✅ 目录结构标准清单解析成功。")
            self.info.append("📋 已从目录结构标准清单.md加载检查标准")
        else:
            self.issues.append(
                "❌ 错误：未能解析目录结构标准清单或清单为空。请检查 docs/01-设计/目录结构标准清单.md 文件。")
            print("❌ 错误：未能解析目录结构标准清单或清单为空。")
            self.warnings.append(
                "⚠️ 未能从目录结构标准清单.md加载标准，或标准文件格式不正确，将使用备用硬编码标准。")
            self.standard_structure = get_fallback_structure()
            # 如果使用 fallback，需要重新初始化白名单路径为小写
            raw_required_dirs_fallback = self.standard_structure.get(
                "required_dirs", [])
            raw_required_files_map_fallback = self.standard_structure.get(
                "required_files", {})
            self.whitelist_dirs_str_lower = set(
                d.lower() for d in raw_required_dirs_fallback)
            self.required_files_map_lower_keys = {
                k.lower(): v for k, v in raw_required_files_map_fallback.items()}
            self.whitelist_files_str_lower = set(
                self.required_files_map_lower_keys.keys())
            self.whitelist_dirs_pathobj = {
                Path(p) for p in self.whitelist_dirs_str_lower}
            self.whitelist_files_pathobj = {
                Path(p) for p in self.whitelist_files_str_lower}

    def check_all(self) -> Dict:
        """执行所有检查"""
        print("🔍 开始检查项目目录结构...")

        # 白名单路径已在 __init__ 中处理为小写 Path 对象
        # whitelist_dirs_pathobj = self.whitelist_dirs_pathobj
        # whitelist_files_pathobj = self.whitelist_files_pathobj

        # 1. 获取项目中实际存在的所有文件和目录 (Path对象，相对于项目根目录，且已转为小写)
        actual_project_paths_relative_lower = set()  # 使用 set 确保唯一性

        # 从配置文件中读取排除目录
        excluded_for_scan_entirely = set(
            CONFIG.get(
                'structure_check',
                {}).get(
                'excluded_dirs',
                [
                    '.git',
                    '.hg',
                    '.svn',
                    'node_modules',
                    '__pycache__',
                    '.pytest_cache',
                    '.mypy_cache',
                    'build',
                    'dist',
                    '*.egg-info']))
        self.info.append(
            f"📋 从配置文件加载排除目录: {
                ', '.join(excluded_for_scan_entirely)}")

        for path_object in self.project_root.rglob("*"):
            try:
                # 获取相对路径字符串并立即转为小写
                relative_path_str_lower = str(
                    path_object.relative_to(
                        self.project_root)).lower()
                # 从小写字符串创建 Path 对象
                relative_path_lower = Path(relative_path_str_lower)

                # 检查是否在完全排除扫描的目录中 (基于小写路径的parts)
                if any(
                        part.lower() in excluded_for_scan_entirely for part in relative_path_lower.parts):
                    continue

                actual_project_paths_relative_lower.add(relative_path_lower)

            except ValueError:
                continue  # 忽略不在项目根目录下的路径

        # 分别获取实际的目录和文件集合 (基于小写 Path 对象)
        actual_dirs_relative_lower = {
            p for p in actual_project_paths_relative_lower if (
                self.project_root / p).is_dir()}
        actual_files_relative_lower = {
            p for p in actual_project_paths_relative_lower if (
                self.project_root / p).is_file()}

        # 2. 检查必需项是否存在 (白名单中的项是否在实际项目中，全部使用小写路径比较)
        self.check_required_directories(
            actual_dirs_relative_lower,
            self.whitelist_dirs_pathobj)
        self.check_required_files(
            actual_files_relative_lower,
            self.whitelist_files_pathobj)

        # 3. 检查冗余项 (实际项目中的项是否在白名单中，全部使用小写路径比较)
        # 注意：传递给 check_redundant_items 的 actual_project_paths_relative_lower
        # 已经是小写 Path 对象集合
        self.check_redundant_items(
            actual_project_paths_relative_lower,
            self.whitelist_dirs_pathobj,
            self.whitelist_files_pathobj)

        # 4. 其他检查 (只针对实际存在的、且未被完全扫描排除的项)
        #    获取用于其他检查的路径列表 (Path对象，绝对路径，但其相对部分已小写化以用于排除检查)
        paths_for_other_checks = []
        print(f"项目根目录: {self.project_root}")

        # 确保即使在必需目录缺失的情况下，也会继续执行命名规范和禁止项模式的检查
        # 使用实际检查的目录，而不是PROJECT_ROOT
        for path_object in self.project_root.rglob("*"):
            try:
                # 获取相对路径字符串
                relative_path_str = str(
                    path_object.relative_to(
                        self.project_root))

                # 检查是否在完全排除扫描的目录中
                if any(
                        part in excluded_for_scan_entirely for part in path_object.parts):
                    continue

                # 添加路径到其他检查列表
                paths_for_other_checks.append(path_object)

            except ValueError:
                continue  # 忽略不在项目根目录下的路径

        print(f"其他检查路径数量: {len(paths_for_other_checks)}")
        if len(paths_for_other_checks) == 0:
            print("警告: 没有找到任何路径进行其他检查，请检查项目根目录是否正确。")

        # 5. 专门检查项目根目录规范
        self.check_root_directory_compliance()

        self.check_forbidden_items(paths_for_other_checks)
        self.check_naming_conventions(paths_for_other_checks)
        self.check_file_content_basic()  # 这个方法目前是 pass

        # 生成报告
        report = self.generate_report()

        # 保存报告
        report_dir = self.project_root / \
            CONFIG['structure_check']['report_dir']
        report_filename_format = CONFIG['structure_check']['report_name_format']
        self.save_report(report, report_dir, report_filename_format)

        return report

    def check_required_directories(
            self,
            actual_dirs_relative_lower: set,
            whitelist_dirs_pathobj: set):
        """检查必需的目录 (白名单中的目录是否存在，使用小写路径比较)"""
        print("📁 检查必需目录 (白名单核对)...")
        for required_dir_path_obj_lower in whitelist_dirs_pathobj:  # 已经是小写Path对象
            if required_dir_path_obj_lower not in actual_dirs_relative_lower:
                self.missing_items.append(
                    f"预期目录缺失: {str(required_dir_path_obj_lower)}")
            else:
                self.info.append(
                    f"✅ 白名单目录存在: {
                        str(required_dir_path_obj_lower)}")

    def check_required_files(self,
                             actual_files_relative_lower: set,
                             whitelist_files_pathobj: set):
        """检查必需的文件 (白名单中的文件是否存在，使用小写路径比较)"""
        print("📄 检查必需文件 (白名单核对)...")
        for required_file_path_obj_lower in whitelist_files_pathobj:  # 已经是小写Path对象
            # 从 self.required_files_map_lower_keys 获取描述，键是小写路径字符串
            description = self.required_files_map_lower_keys.get(
                str(required_file_path_obj_lower), "项目文件")

            if required_file_path_obj_lower not in actual_files_relative_lower:
                self.missing_items.append(
                    f"预期文件缺失: {
                        str(required_file_path_obj_lower)} ({description})")
            elif (self.project_root / required_file_path_obj_lower).stat().st_size == 0:
                self.warnings.append(
                    f"文件为空: {
                        str(required_file_path_obj_lower)}")
            else:
                self.info.append(
                    f"✅ 白名单文件存在且非空: {
                        str(required_file_path_obj_lower)}")

    def check_redundant_items(
            self,
            actual_project_paths_relative_lower: set,
            whitelist_dirs_pathobj: set,
            whitelist_files_pathobj: set):
        """检查冗余项 (实际存在但不在白名单中的项，使用小写路径比较)"""
        print("🗑️  检查冗余项 (非白名单内容)...")

        # excluded_dirs_for_redundancy_check 中的项也应该用小写比较
        excluded_dirs_for_redundancy_check_lower = {
            d.lower() for d in self.excluded_dirs_for_redundancy_check}

        for actual_path_obj_lower in actual_project_paths_relative_lower:  # 已经是小写Path对象
            is_in_excluded_for_redundancy = False
            if actual_path_obj_lower.parts:
                # actual_path_obj_lower.parts[0] 已经是小写
                if actual_path_obj_lower.parts[0] in excluded_dirs_for_redundancy_check_lower:
                    is_in_excluded_for_redundancy = True

            if is_in_excluded_for_redundancy:
                continue

            # 使用 self.project_root / actual_path_obj_lower 来检查实际文件系统中的项
            # 因为 actual_path_obj_lower 是小写的，而文件系统上的原始路径可能有大写
            # 但 is_dir() / is_file() 在Windows上通常不区分大小写，所以这里应该没问题
            # 为了更严谨，应该用原始大小写的路径去is_dir/is_file，但我们这里只有小写路径
            # 更好的做法是在收集 actual_project_paths_relative 时同时保存原始大小写路径和对应的小写路径
            # 但目前为了简化，先假设 is_dir/is_file 在小写路径上能正确工作
            is_dir = (self.project_root / actual_path_obj_lower).is_dir()
            is_file = (self.project_root / actual_path_obj_lower).is_file()

            is_redundant = False
            if is_dir:
                if actual_path_obj_lower not in whitelist_dirs_pathobj:
                    is_redundant = True
            elif is_file:
                if actual_path_obj_lower not in whitelist_files_pathobj:
                    is_redundant = True

            if is_redundant:
                item_type = "目录" if is_dir else "文件"
                # 添加到 set 的冗余信息字符串中的路径也使用小写
                redundancy_msg = f"冗余{item_type}: {str(actual_path_obj_lower)}"
                self.redundant_items.add(redundancy_msg)

    def check_forbidden_items(self, paths_to_check: list):
        """检查禁止项 (例如 .tmp, .bak 文件)"""
        print("🚫 检查禁止项...")
        print(f"待检查路径数量: {len(paths_to_check)}")
        forbidden_patterns = self.standard_structure.get(
            "forbidden_patterns", [])
        if not forbidden_patterns:
            # 如果没有定义禁止模式，从配置文件中读取默认的禁止模式
            default_forbidden_patterns = CONFIG.get('structure_check', {}).get('default_forbidden_patterns', [
                "*.tmp",   # 临时文件
                "*.bak",   # 备份文件
                "*.swp",   # vim交换文件
                "*.log",   # 日志文件
                "*~",      # 临时备份文件
                "Thumbs.db",  # Windows缩略图数据库
                ".DS_Store"  # macOS目录元数据
            ])
            forbidden_patterns = default_forbidden_patterns
            self.info.append(
                f"⚠️ 未在标准文件中定义禁止项模式，使用配置文件中的默认禁止模式: {
                    ', '.join(forbidden_patterns)}")
            print(
                f"⚠️ 未在标准文件中定义禁止项模式，使用配置文件中的默认禁止模式: {
                    ', '.join(forbidden_patterns)}")

        print(f"禁止项模式: {forbidden_patterns}")
        found_forbidden_items = False
        forbidden_items_count = 0

        if not paths_to_check:
            print("没有找到需要检查的路径")
            return

        print("\n开始逐个检查路径是否包含禁止项...")
        print("=" * 50)

        for i, path_obj in enumerate(paths_to_check):
            print(f"\n检查第{i + 1}个路径: {path_obj}")
            try:
                path_str = str(path_obj.relative_to(self.project_root))
                print(f"相对路径: {path_str}")

                # 检查是否匹配任何禁止模式
                matched_patterns = []
                for pattern in forbidden_patterns:
                    print(f"检查模式: {pattern}")
                    match_path = fnmatch.fnmatch(
                        path_str.lower(), pattern.lower())
                    match_name = fnmatch.fnmatch(
                        path_obj.name.lower(), pattern.lower())
                    print(f"  路径匹配结果: {match_path}, 文件名匹配结果: {match_name}")

                    if match_path or match_name:
                        matched_patterns.append(pattern)

                if matched_patterns:
                    issue_msg = f"发现禁止项: {
                        path_obj.relative_to(
                            self.project_root)} (匹配模式: {
                        ', '.join(matched_patterns)})"
                    self.issues.append(issue_msg)
                    print(f"❌ {issue_msg}")
                    found_forbidden_items = True
                    forbidden_items_count += 1
                else:
                    print(f"✅ 未发现禁止项: {path_str}")
            except ValueError as e:
                # 如果路径不在项目根目录下，跳过
                print(f"无法获取相对路径: {path_obj}，错误: {e}")
                continue

        print("\n" + "=" * 50)
        print("禁止项检查结果汇总:")

        if found_forbidden_items:
            print(f"发现禁止项问题，总计: {forbidden_items_count}个严重问题")
            print("错误列表:")
            for i, error in enumerate(
                    [e for e in self.issues if "发现禁止项" in e]):
                print(f"  {i + 1}. {error}")
        else:
            print("未发现禁止项问题")

        print(f"禁止项检查完成，严重问题总数: {forbidden_items_count}")

    def check_root_directory_compliance(self):
        """检查项目根目录规范合规性"""
        print("🏠 检查项目根目录规范合规性...")

        # 从配置文件中读取根目录规则
        root_rules = CONFIG.get(
            'structure_check', {}).get(
            'root_directory_rules', {})
        if not root_rules:
            self.warnings.append("⚠️ 未配置根目录检查规则，跳过根目录规范检查")
            return

        allowed_directories = set(root_rules.get('allowed_directories', []))
        forbidden_dir_patterns = root_rules.get(
            'forbidden_directory_patterns', [])
        forbidden_file_patterns = root_rules.get('forbidden_file_patterns', [])

        print(f"允许的根目录: {', '.join(allowed_directories)}")
        print(f"禁止的目录模式: {', '.join(forbidden_dir_patterns)}")
        print(f"禁止的文件模式: {', '.join(forbidden_file_patterns)}")

        # 检查根目录下的直接子项
        root_violations = []

        try:
            for item in self.project_root.iterdir():
                item_name = item.name

                if item.is_dir():
                    # 检查目录是否在允许列表中
                    if item_name not in allowed_directories:
                        # 检查是否匹配禁止模式
                        is_forbidden = False
                        for pattern in forbidden_dir_patterns:
                            if fnmatch.fnmatch(
                                    item_name.lower(), pattern.lower()):
                                is_forbidden = True
                                root_violations.append(
                                    f"根目录禁止目录: {item_name} (匹配模式: {pattern})")
                                break

                        if not is_forbidden:
                            root_violations.append(
                                f"根目录非标准目录: {item_name} (不在允许列表中)")
                    else:
                        self.info.append(f"✅ 根目录标准目录: {item_name}")

                elif item.is_file():
                    # 检查文件是否匹配禁止模式
                    for pattern in forbidden_file_patterns:
                        if fnmatch.fnmatch(item_name.lower(), pattern.lower()):
                            root_violations.append(
                                f"根目录禁止文件: {item_name} (匹配模式: {pattern})")
                            break
                    else:
                        # 根目录一般不应该有文件（除了特殊情况如README等）
                        if item_name.lower() not in [
                                'readme.md', 'readme.txt', '.gitignore', 'license']:
                            root_violations.append(
                                f"根目录不规范文件: {item_name} (建议移至适当目录)")

        except Exception as e:
            self.warnings.append(f"⚠️ 检查根目录时发生错误: {e}")
            return

        # 记录违规项
        if root_violations:
            for violation in root_violations:
                self.issues.append(f"根目录规范违规: {violation}")
            print(f"❌ 发现 {len(root_violations)} 个根目录规范违规")
        else:
            self.info.append("✅ 根目录规范检查通过")
            print("✅ 根目录规范检查通过")

    def check_naming_conventions(self, paths_to_check: list):
        """检查命名规范"""
        print("🏷️ 检查命名规范...")
        print(f"待检查路径数量: {len(paths_to_check)}")
        naming_rules = self.standard_structure.get("naming_rules", {})
        if not naming_rules:
            self.info.append("⚠️ 未定义命名规范，跳过命名规范检查")
            print("⚠️ 未定义命名规范，跳过命名规范检查")
            return

        print(f"命名规范: {naming_rules}")

        # 从配置文件中读取默认的命名规则
        default_naming_rules = CONFIG.get(
            'structure_check', {}).get(
            'default_naming_rules', {})

        # 定义各类文件的正则表达式规则
        rules = {
            "docs": {
                "pattern": default_naming_rules.get(
                    "docs",
                    r"^[\u4e00-\u9fa5a-zA-Z0-9_\-\s\.]+\.(md|txt|docx|pdf)$"),
                "description": "文档文件应使用中文命名，可包含字母、数字、下划线、短横线和空格"},
            "code": {
                "pattern": default_naming_rules.get(
                    "tools",
                    r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$"),
                "description": "代码文件应使用小写字母和下划线(snake_case)，以字母开头"},
            "config": {
                "pattern": default_naming_rules.get(
                    "config",
                    r"^[a-z0-9_\-\.]+$"),
                "description": "配置文件应使用小写字母，可包含数字、下划线、短横线和点"},
            "directory": {
                "pattern": r"^[a-z0-9_\-\u4e00-\u9fa5\s]+$",
                "description": "目录应使用小写字母和下划线，或中文命名，可包含数字、短横线和空格"}}

        self.info.append(f"📋 从配置文件加载命名规则: {default_naming_rules}")

        print(f"正则表达式规则: {rules}")

        # 文件扩展名分类
        doc_extensions = [
            ".md",
            ".txt",
            ".docx",
            ".pd",
            ".xlsx",
            ".pptx",
            ".csv"]
        code_extensions = [
            ".py",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".go",
            ".rs",
            ".php",
            ".sh",
            ".bat",
            ".ps1"]
        config_extensions = [
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".ini",
            ".con",
            ".config",
            ".env"]

        print("文件扩展名分类:")
        print(f"  文档文件: {doc_extensions}")
        print(f"  代码文件: {code_extensions}")
        print(f"  配置文件: {config_extensions}")

        # 从配置文件中读取跳过检查的目录
        skip_dirs = CONFIG.get(
            'structure_check', {}).get(
            'excluded_dirs', [
                "bak", "logs", ".git", ".vscode", "__pycache__", "node_modules"])
        print(f"跳过检查的目录: {skip_dirs}")
        self.info.append(f"📋 命名规范检查跳过目录: {', '.join(skip_dirs)}")

        found_naming_issues = False
        naming_warnings_count = 0

        if not paths_to_check:
            print("没有找到需要检查的路径")
            return

        print("\n开始逐个检查路径的命名规范...")
        print("=" * 50)

        for i, path_obj in enumerate(paths_to_check):
            print(f"\n检查第{i + 1}个路径: {path_obj}")
            try:
                rel_path = path_obj.relative_to(self.project_root)

                # 跳过特定目录下的文件检查
                if any(part.lower() in skip_dirs for part in rel_path.parts):
                    print(f"跳过路径: {rel_path} (在跳过检查的目录中)")
                    continue

                print(f"检查路径: {rel_path}")

                if path_obj.is_dir():
                    rule = rules["directory"]
                    print(f"目录检查: {path_obj.name}, 使用规则: {rule['pattern']}")
                    match_result = re.match(rule["pattern"], path_obj.name)
                    print(f"匹配结果: {match_result is not None}")

                    if not match_result:
                        warning_msg = f"目录命名不规范: {rel_path} ({
                            rule['description']})"
                        self.warnings.append(warning_msg)
                        print(f"⚠️ {warning_msg}")
                        found_naming_issues = True
                        naming_warnings_count += 1
                    else:
                        print(f"✅ 目录命名规范: {rel_path}")
                elif path_obj.is_file():
                    ext = path_obj.suffix.lower()
                    print(f"文件扩展名: {ext}")

                    if ext in doc_extensions:
                        rule = rules["docs"]
                        print(f"文档文件: {rel_path}, 使用规则: {rule['pattern']}")
                    elif ext in code_extensions:
                        rule = rules["code"]
                        print(f"代码文件: {rel_path}, 使用规则: {rule['pattern']}")
                    elif ext in config_extensions:
                        rule = rules["config"]
                        print(f"配置文件: {rel_path}, 使用规则: {rule['pattern']}")
                    else:
                        print(f"未知类型文件: {rel_path}，跳过检查")
                        continue

                    # 检查文件名是否符合规则
                    print(f"检查文件名: {path_obj.name}")
                    match_result = re.match(rule["pattern"], path_obj.name)
                    print(f"匹配结果: {match_result is not None}")

                    if not match_result:
                        warning_msg = f"文件命名不规范: {rel_path} ({
                            rule['description']})"
                        self.warnings.append(warning_msg)
                        print(f"⚠️ {warning_msg}")
                        found_naming_issues = True
                        naming_warnings_count += 1
                    else:
                        print(f"✅ 文件命名规范: {rel_path}")
            except ValueError as e:
                print(f"无法获取相对路径: {path_obj}，错误: {e}")
                continue

        print("\n" + "=" * 50)
        print("命名规范检查结果汇总:")

        if found_naming_issues:
            print(f"发现命名规范问题，总计: {naming_warnings_count}个警告")
            print("警告列表:")
            for i, warning in enumerate(
                    [w for w in self.warnings if "命名不规范" in w]):
                print(f"  {i + 1}. {warning}")
        else:
            print("未发现命名规范问题")

        print(f"命名规范检查完成，警告总数: {naming_warnings_count}")

    def check_file_content_basic(self):
        """基础文件内容检查 (例如, 检查必需文件是否为空) - 部分已移至 check_required_files"""
        print("📜 基础文件内容检查 (当前跳过)...")
        # 部分逻辑已在 check_required_files 中处理空文件的情况
        # 此处可以保留用于未来更复杂的内容检查，例如特定标记或头部信息
        pass

    def generate_report(self) -> Dict:
        """生成检查报告"""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_redundant = len(self.redundant_items)
        total_missing = len(self.missing_items)
        total_info = len(self.info)

        # 计算得分，更细致的扣分策略
        score = 100
        score -= total_issues * 15  # 每个严重问题扣15分
        score -= total_redundant * 10  # 每个冗余项扣10分
        score -= total_warnings * 5   # 每个警告扣5分
        score -= total_missing * 2    # 每个缺失项扣2分 (轻微)
        score = max(0, score)  # 最低0分

        # 确定状态，更清晰的状态层级
        if total_issues > 0 or total_redundant > 0:
            status_icon = "❌"
            status_text = "检查失败"
            if total_issues > 0 and total_redundant > 0:
                status_detail = "存在严重问题和冗余项"
            elif total_issues > 0:
                status_detail = "存在严重问题"
            else:
                status_detail = "存在冗余项"
        elif total_warnings > 0:
            status_icon = "⚠️"
            status_text = "通过但有警告"
            status_detail = "存在警告信息"
        elif total_missing > 0:
            status_icon = "ℹ️"
            status_text = "通过但有缺失项"
            status_detail = "存在预期但缺失的项"
        else:
            status_icon = "✅"
            status_text = "完全通过"
            status_detail = "所有检查项符合标准"

        final_status = f"{status_icon} {status_text} - {status_detail}"
        if total_missing > 0 and (
                total_issues == 0 and total_redundant == 0 and total_warnings == 0):
            final_status = f"{status_icon} {status_text} - {status_detail} (请注意补充缺失项)"
        elif total_missing > 0 and total_warnings > 0 and (total_issues == 0 and total_redundant == 0):
            final_status = f"{status_icon} {status_text} - {status_detail} (请注意补充缺失项和处理警告)"

        # 从配置文件中读取标准清单文件路径
        standard_list_file = CONFIG.get(
            'structure_check', {}).get(
            'standard_list_file', 'docs/01-设计/目录结构标准清单.md')
        standard_file_path = PROJECT_ROOT / standard_list_file

        report = {
            "check_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_root_checked": str(self.project_root),
            "standard_file_used": str(standard_file_path),
            "overall_status": final_status,
            "final_score": score,
            "summary_counts": {
                "total_issues": total_issues,
                "total_warnings": total_warnings,
                "total_redundant_items": total_redundant,
                "total_missing_items": total_missing,
                "total_info_logs": total_info,
                "total_items_scanned": total_issues + total_warnings + total_redundant + total_missing + total_info  # 粗略估计扫描点
            },
            "detailed_findings": {
                "critical_issues": self.issues,
                "improvement_warnings": self.warnings,
                "unnecessary_items": sorted(list(self.redundant_items)),
                "missing_required_items": self.missing_items,
                "informational_logs": self.info,
            },
        }
        return report

    def save_report(
            self,
            report: Dict,
            report_dir: Path,
            report_filename_format: str):
        """保存检查报告到文件"""
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
            # 从报告内部获取时间戳，确保文件名与报告内容一致
            report_timestamp_str = datetime.strptime(
                report["check_timestamp"],
                "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S")

            if "{timestamp}" in report_filename_format:
                report_file_name = report_filename_format.format(
                    timestamp=report_timestamp_str)
            elif "{status}" in report_filename_format:  # 增加按状态保存的选项
                # 从 overall_status 中提取一个简短的状态描述作为文件名的一部分
                # 例如 "❌ 检查失败 - 存在严重问题" -> "检查失败"
                status_for_filename = report["overall_status"].split(
                    " - ")[0].split(" ")[-1]  # 取最后一个词
                base, ext = os.path.splitext(
                    report_filename_format.format(
                        status=status_for_filename))
                report_file_name = f"{base}_{report_timestamp_str}{ext}"
            else:
                base, ext = os.path.splitext(report_filename_format)
                report_file_name = f"{base}_{report_timestamp_str}{ext}"

            report_file_path = report_dir / report_file_name

            with open(report_file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=4)

            success_msg = f"📝 结构检查报告已成功保存至: {report_file_path}"
            print(success_msg)
            # 避免在保存报告成功后修改报告内容 (self.info)
            # self.info.append(success_msg) # 移至调用方或日志模块处理
            return str(report_file_path)  # 返回保存的路径

        except KeyError as e:
            error_msg = f"❌ 保存报告失败: 报告数据中缺少键 '{e}'。请检查 generate_report 方法。"
            print(error_msg)
            self.issues.append(error_msg)
            return None
        except IOError as e:
            error_msg = f"❌ 保存报告失败: 无法写入文件。IO错误: {e}"
            print(error_msg)
            self.issues.append(error_msg)
            return None
        except Exception as e:
            error_msg = f"❌ 保存报告时发生未知错误: {e}"
            print(error_msg)
            self.issues.append(error_msg)
            import traceback
            traceback.print_exc()  # 打印详细堆栈信息以供调试
            return None

    def format_report_for_console(self, report: Dict) -> str:
        """格式化报告为控制台可读文本，更简洁"""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("========   3AI工作室 - 项目结构健康检查报告   ========")
        lines.append("=" * 70)
        lines.append(f"检查时间:         {report['check_timestamp']}")
        lines.append(f"项目根目录:       {report['project_root_checked']}")
        lines.append(f"遵循标准:         {report['standard_file_used']}")
        lines.append(f"综合评估:         {report['overall_status']}")
        lines.append(f"健康指数:         {report['final_score']}/100")
        lines.append("-" * 70)

        summary = report["summary_counts"]
        lines.append("📊 核心指标统计:")
        lines.append(
            f"  - 🔴 严重问题 (Critical Issues):      {summary['total_issues']}")
        lines.append(
            f"  - 🟡 改进警告 (Improvement Warnings): {summary['total_warnings']}")
        lines.append(
            f"  - 🗑️ 冗余项 (Unnecessary Items):      {summary['total_redundant_items']}")
        lines.append(
            f"  - ℹ️ 缺失项 (Missing Required):      {summary['total_missing_items']}")
        lines.append(
            f"  - 📋 信息记录 (Info Logs):          {summary['total_info_logs']}")
        lines.append(
            f"  - 🔍 总扫描点 (Estimated Scanned): {summary['total_items_scanned']}")
        lines.append("-" * 70)

        details = report["detailed_findings"]

        if details["critical_issues"]:
            lines.append("🔴 严重问题 (Critical Issues - 需立即处理):")
            for idx, issue in enumerate(details["critical_issues"], 1):
                lines.append(f"  {idx}. {issue}")
            lines.append("")

        if details["unnecessary_items"]:
            lines.append("🗑️ 冗余项 (Unnecessary Items - 建议清理):")
            for idx, item in enumerate(details["unnecessary_items"], 1):
                lines.append(f"  {idx}. {item}")
            lines.append("")

        if details["improvement_warnings"]:
            lines.append("🟡 改进警告 (Improvement Warnings - 建议关注):")
            for idx, warning in enumerate(details["improvement_warnings"], 1):
                lines.append(f"  {idx}. {warning}")
            lines.append("")

        if details["missing_required_items"]:
            lines.append("ℹ️ 预期但缺失的项 (Missing Required Items - 请补充):")
            for idx, item in enumerate(details["missing_required_items"], 1):
                lines.append(f"  {idx}. {item}")
            lines.append("")

        # 信息记录通常用于调试或确认，默认不在控制台大量输出，除非有特殊需要
        # if details["informational_logs"]:
        #     lines.append("📋 信息记录 (Informational Logs):")
        #     for idx, info_log in enumerate(details["informational_logs"], 1):
        #         lines.append(f"  {idx}. {info_log}")
        #     lines.append("")

        lines.append("=" * 70)
        lines.append("========             报告结束             ========")
        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def print_report_to_console(self, report: Dict):
        """将格式化后的报告打印到控制台"""
        formatted_report_text = self.format_report_for_console(report)
        print(formatted_report_text)


def main():
    """主函数"""
    try:
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="3AI工作室目录结构检查工具")
        parser.add_argument(
            "project_path",
            nargs="?",
            default=".",
            help="项目根目录路径")
        parser.add_argument(
            "--only-check-forbidden",
            action="store_true",
            help="仅检查禁止项")
        parser.add_argument(
            "--report-only",
            action="store_true",
            help="仅生成报告，不执行检查")
        parser.add_argument("--verbose", action="store_true", help="显示详细输出")
        args = parser.parse_args()

        # 使用传入的路径，如果它是相对路径，则相对于当前工作目录解析
        project_root_abs = Path(args.project_path).resolve()
        if not project_root_abs.is_dir():
            print(
                f"❌错误：提供的项目路径 '{
                    args.project_path}' (解析为 '{project_root_abs}') 不是一个有效的目录。")
            sys.exit(4)

        checker = StructureChecker(project_root_abs)  # 使用解析后的绝对路径

        if args.only_check_forbidden:
            # 仅执行禁止项检查
            print("🔍 仅执行禁止项检查...")
            paths_to_check = []

            # 从配置文件中读取排除目录
            excluded_for_scan_entirely = set(
                CONFIG.get(
                    'structure_check',
                    {}).get(
                    'excluded_dirs',
                    [
                        '.git',
                        '.hg',
                        '.svn',
                        'node_modules',
                        '__pycache__',
                        '.pytest_cache',
                        '.mypy_cache',
                        'build',
                        'dist',
                        '*.egg-info']))
            print(f"📋 从配置文件加载排除目录: {', '.join(excluded_for_scan_entirely)}")

            for path_object in project_root_abs.rglob("*"):
                try:
                    # 检查是否在完全排除扫描的目录中
                    if any(
                            part in excluded_for_scan_entirely for part in path_object.parts):
                        continue
                    paths_to_check.append(path_object)
                except ValueError:
                    continue  # 忽略不在项目根目录下的路径

            checker.check_forbidden_items(paths_to_check)

            # 生成简化报告
            # 计算得分 - 禁止项模式下，每个禁止项扣20分，最低0分
            score = max(0, 100 - len(checker.issues) * 20)
            # 从配置文件中读取标准清单文件路径
            standard_list_file = CONFIG.get(
                'structure_check', {}).get(
                'standard_list_file', 'docs/01-设计/目录结构标准清单.md')
            standard_file_path = PROJECT_ROOT / standard_list_file

            report_data = {
                "check_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "project_root_checked": str(project_root_abs),
                "standard_file_used": str(standard_file_path),
                "overall_status": "✅ 检查通过" if not checker.issues else f"❌ 检查失败 - 发现{len(checker.issues)}个禁止项",
                "final_score": score,  # 添加得分字段
                "summary_counts": {
                    "total_issues": len(checker.issues),
                    "total_warnings": 0,
                    "total_redundant_items": 0,
                    "total_missing_items": 0,
                    "total_info_logs": len(checker.info),
                    "total_items_scanned": len(paths_to_check)
                },
                "detailed_findings": {
                    "critical_issues": checker.issues,
                    "improvement_warnings": [],
                    "unnecessary_items": [],
                    "missing_required_items": [],
                    "informational_logs": checker.info,
                },
            }

            # 打印报告到控制台
            checker.print_report_to_console(report_data)

            # 根据报告中的 issues 返回适当的退出码
            if len(checker.issues) > 0:
                sys.exit(1)  # 有禁止项问题
            else:
                sys.exit(0)  # 完全通过
        else:
            # 执行完整检查
            report_data = checker.check_all()

            # 打印报告到控制台
            checker.print_report_to_console(report_data)

            # 根据报告中的 summary_counts 返回适当的退出码
            summary_counts = report_data.get("summary_counts", {})
            if summary_counts.get(
                    "total_issues",
                    0) > 0 or summary_counts.get(
                    "total_redundant_items",
                    0) > 0:
                sys.exit(1)  # 有严重问题或冗余项
            elif summary_counts.get("total_warnings", 0) > 0:
                sys.exit(2)  # 有警告
            elif summary_counts.get("total_missing_items", 0) > 0:
                sys.exit(0)  # 通过但有缺失项，也算通过，但提示用户
            else:
                sys.exit(0)  # 完全通过

    except IndexError:
        print("❌ 错误: 请提供项目根目录作为命令行参数。")
        print("用法: python check_structure.py /path/to/your/project")
        sys.exit(4)  # 参数错误
    except Exception as e:
        print(f"❌ 检查过程中发生未预料的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)  # 其他错误


if __name__ == "__main__":
    main()
