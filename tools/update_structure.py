#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3AI工作室目录结构快照生成工具

功能：
1. 扫描当前项目目录结构
2. 生成符合标准格式的目录结构清单
3. 将快照保存为markdown格式的标准清单文件
4. 支持增量更新现有标准清单
5. 自动分类文件类型和用途

使用方法：
    python tools/update_structure.py
    python tools/update_structure.py --output docs/目录结构标准清单.md
    python tools/update_structure.py --update  # 更新现有清单

作者：雨俊
版本：2.0
更新：2025-06-13
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
# from typing import List, Dict, Set  # 暂时注释未使用的导入

# 导入错误处理机制
from exceptions import ValidationError, ErrorHandler

# 初始化日志和错误处理器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
error_handler = ErrorHandler()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 需要忽略的目录和文件
IGNORE_PATTERNS = {
    # 系统文件
    '.git', '.gitignore', '.vscode', '__pycache__', '*.pyc', '*.pyo',
    # 临时文件
    '*.tmp', '*.temp', '*.bak', '*.backup', '*.swp', '*.swo',
    # 日志文件（但保留logs目录）
    '*.log',
    # 编译文件
    '*.exe', '*.dll', '*.so', '*.dylib',
    # 压缩文件
    '*.zip', '*.rar', '*.7z', '*.tar', '*.gz'
}

# 文件类型分类
FILE_CATEGORIES = {
    'docs': ['.md', '.txt', '.doc', '.docx', '.pd'],
    'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs'],
    'config': ['.json', '.yaml', '.yml', '.ini', '.cfg', '.con'],
    'data': ['.csv', '.xlsx', '.xls', '.db', '.sqlite'],
    'image': ['.png', '.jpg', '.jpeg', '.gi', '.svg', '.ico'],
    'other': []
}


class DirectorySnapshotter:
    """目录结构快照生成器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.directories = set()
        self.files = {}
        self.template_files = set()

    def should_ignore(self, path: Path) -> bool:
        """判断是否应该忽略某个路径"""
        name = path.name

        # 检查忽略模式
        for pattern in IGNORE_PATTERNS:
            if pattern.startswith('*.'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True

        return False

    def categorize_file(self, file_path: Path) -> str:
        """对文件进行分类"""
        suffix = file_path.suffix.lower()

        for category, extensions in FILE_CATEGORIES.items():
            if suffix in extensions:
                return category

        return 'other'

    def get_file_description(self, file_path: Path) -> str:
        """获取文件描述"""
        rel_path = file_path.relative_to(self.project_root)

        # 特殊文件的描述
        special_descriptions = {
            'docs/01-核心文档/项目目标定义.md': '项目目标和范围定义',
            'docs/01-核心文档/开发任务书.md': '详细开发任务说明',
            'docs/01-核心文档/目录结构标准清单.md': '项目目录结构标准',
            'docs/02-项目管理/工作完成检查清单.md': '项目完成度检查',
            'docs/02-项目管理/问题解决记录.md': '开发过程问题记录',
            'docs/02-项目管理/进度跟踪表.md': '项目进度管理',
            'docs/03-技术支撑/环境配置说明.md': '开发环境配置指南',
            'docs/03-技术支撑/工具使用指南.md': '开发工具说明',
            'docs/03-技术支撑/部署指南.md': '项目部署说明',
            'tools/structure_check.py': '目录结构检查脚本',
            'tools/update_structure.py': '目录结构快照生成脚本'
        }

        str_path = str(rel_path).replace('\\', '/')
        if str_path in special_descriptions:
            return special_descriptions[str_path]

        # 根据文件类型和位置生成描述
        if 'template' in file_path.name.lower() or '模板' in file_path.name:
            return f"标准{file_path.stem}格式"
        elif file_path.parent.name == '04-模板文件':
            return f"标准{file_path.stem}"
        elif file_path.suffix == '.md':
            return f"{file_path.stem}文档"
        elif file_path.suffix == '.py':
            return f"{file_path.stem}脚本"
        else:
            return f"{file_path.stem}文件"

    def scan_directory(self):
        """扫描项目目录"""
        logger.info("📁 扫描项目目录结构...")

        # 需要排除的目录内容（只保留目录本身）
        excluded_content_dirs = {'bak', 'logs'}

        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)

            # 过滤忽略的目录
            dirs[:] = [
                d for d in dirs if not self.should_ignore(
                    root_path / d)]

            # 记录目录
            if root_path != self.project_root:
                rel_dir = root_path.relative_to(self.project_root)
                rel_dir_str = str(rel_dir).replace('\\', '/')

                # 检查是否是bak或logs的子目录，如果是则跳过记录
                if any(
                    rel_dir_str.startswith(
                        f"{excluded_dir}/") for excluded_dir in excluded_content_dirs):
                    continue

                self.directories.add(rel_dir_str)

            # 记录文件
            for file_name in files:
                file_path = root_path / file_name

                if self.should_ignore(file_path):
                    continue

                rel_path = file_path.relative_to(self.project_root)
                str_path = str(rel_path).replace('\\', '/')

                # 检查文件是否在bak或logs目录下，如果是则跳过记录
                if any(str_path.startswith(f"{excluded_dir}/")
                       for excluded_dir in excluded_content_dirs):
                    continue

                description = self.get_file_description(file_path)
                category = self.categorize_file(file_path)

                self.files[str_path] = {
                    'description': description,
                    'category': category,
                    'size': file_path.stat().st_size if file_path.exists() else 0}

                # 识别模板文件
                if ('template' in file_name.lower() or '模板' in file_name
                        or file_path.parent.name == '04-模板文件'):
                    self.template_files.add(str_path)

    def generate_standard_content(self) -> str:
        """生成标准清单内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = (f"# 3AI工作室目录结构标准清单\n\n"
                   f"> 生成时间: {timestamp}\n"
                   f"> 生成工具: update_structure.py\n\n"
                   f"## 1. 标准目录结构\n\n### 1.1 核心目录\n")

        # 按层级组织目录
        sorted_dirs = sorted(self.directories)
        current_level_dirs = {}

        for dir_path in sorted_dirs:
            parts = dir_path.split('/')
            level = len(parts)

            if level not in current_level_dirs:
                current_level_dirs[level] = []
            current_level_dirs[level].append(dir_path)

        for level in sorted(current_level_dirs.keys()):
            if level == 1:
                content += "\n```\n"
                for dir_path in sorted(current_level_dirs[level]):
                    content += f"{dir_path}/\n"
                content += "```\n"

        # 核心文档清单
        content += "\n## 2. 核心文档清单\n\n### 2.1 必备文档\n\n"

        required_files = []
        template_files = []

        for file_path, info in sorted(self.files.items()):
            if file_path in self.template_files:
                template_files.append((file_path, info['description']))
            elif (file_path.startswith('docs/') and file_path.endswith('.md')
                  and file_path not in self.template_files):
                required_files.append((file_path, info['description']))

        for file_path, description in required_files:
            content += f"- `{file_path}` ({description})\n"

        # 模板文件
        if template_files:
            content += "\n### 2.4 模板文件\n\n"
            for file_path, description in template_files:
                content += f"- `{file_path}` ({description})\n"

        # 禁止创建的目录/文件
        content += "\n## 3. 禁止创建的目录/文件\n\n"
        content += "### 3.1 临时文件\n"
        content += "- `*.tmp`, `*.temp`, `*.bak`, `*.backup`\n"
        content += "- `*.swp`, `*.swo` (编辑器临时文件)\n\n"

        content += "### 3.2 系统文件\n"
        content += "- `__pycache__/`, `*.pyc`, `*.pyo`\n"
        content += "- `.DS_Store`, `Thumbs.db`\n\n"

        content += "### 3.3 日志文件\n"
        content += "- `*.log` (日志文件应放在logs/目录下)\n\n"

        # 文件命名规范
        content += "## 4. 文件命名规范\n\n"
        content += "详细的文件命名规范请参考：`{{PROJECT_ROOT}}/docs/03-管理/规范与流程.md`\n\n"

        # 检查规则
        content += "## 5. 自动检查规则\n\n"
        content += "### 5.1 必需目录检查\n"
        for level in sorted(current_level_dirs.keys()):
            if level == 1:
                for dir_path in sorted(current_level_dirs[level]):
                    content += f"- `{dir_path}/`\n"

        content += "\n### 5.2 必需文件检查\n"
        for file_path, description in required_files:
            content += f"- `{file_path}`\n"

        content += "\n### 5.3 模板文件检查\n"
        for file_path, description in template_files:
            content += f"- `{file_path}`\n"

        content += "\n## 6. 手动检查项\n\n"
        content += "- [ ] 文档内容完整性\n"
        content += "- [ ] 代码注释规范性\n"
        content += "- [ ] 配置文件正确性\n"
        content += "- [ ] 版本控制规范（详见 `规范与流程.md`）\n"

        return content

    def save_standard(self, output_path: Path):
        """保存标准清单"""
        content = self.generate_standard_content()

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 标准清单已保存: {output_path}")
        logger.info("📊 统计信息:")
        logger.info(f"   - 目录数量: {len(self.directories)}")
        logger.info(f"   - 文件数量: {len(self.files)}")
        logger.info(f"   - 模板文件: {len(self.template_files)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成3AI工作室目录结构标准清单')
    parser.add_argument('--output', '-o',
                        default='docs/01-设计/目录结构标准清单.md',
                        help='输出文件路径 (默认: docs/01-设计/目录结构标准清单.md)')
    parser.add_argument('--update', '-u', action='store_true',
                        help='更新现有的标准清单文件')

    args = parser.parse_args()

    try:
        snapshotter = DirectorySnapshotter(PROJECT_ROOT)
        snapshotter.scan_directory()

        output_path = PROJECT_ROOT / args.output

        if args.update and output_path.exists():
            # 备份现有文件到专项备份目录
            backup_dir = PROJECT_ROOT / "bak" / "专项备份"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / \
                f'目录结构标准清单.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'

            # 复制文件到备份目录而不是重命名
            import shutil
            shutil.copy2(output_path, backup_path)
            logger.info(f"📋 已备份现有文件到: {backup_path}")

        snapshotter.save_standard(output_path)

    except Exception as e:
        error_handler.handle_error(ValidationError(f"生成过程中发生错误: {e}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
