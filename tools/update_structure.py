#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构更新工具

功能:
- 扫描项目目录结构
- 生成标准化的目录结构清单
- 支持排除特定目录和文件
- 生成Markdown格式的结构文档

作者: 雨俊
创建时间: 2024-12-20
最后更新: 2025-06-25
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import yaml

# 导入工具模块
from utils import get_project_root

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class DirectoryStructureGenerator:
    """目录结构生成器"""

    def __init__(self):
        # 加载配置文件
        self.config = self._load_config()
        
        # 从配置文件中获取排除规则
        structure_config = self.config.get('structure_check', {})
        
        self.excluded_dirs = set(structure_config.get('excluded_dirs', [
            '__pycache__', '.git', '.vscode', '.idea', 'node_modules',
            '.pytest_cache', '.coverage', 'htmlcov', 'dist', 'build',
            '*.egg-info', '.tox', '.mypy_cache', '.DS_Store',
            'Thumbs.db', '.venv', 'venv', 'env'
        ]))

        self.excluded_files = set(structure_config.get('excluded_files', [
            '.gitkeep', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '*.so', '*.dylib', '*.dll'
        ]))
        
        # 允许的隐藏文件/目录
        self.allowed_hidden_items = set(structure_config.get('allowed_hidden_items', [
            '.env', '.env.example', '.gitignore', '.dockerignore',
            '.eslintrc.js', '.prettierrc', '.pre-commit-config.yaml',
            '.devcontainer', '.github', '.venv'
        ]))
        
        # 特殊目录配置
        self.special_dirs = structure_config.get('special_dirs', {
            'bak': ['github_repo', '迁移备份', '专项备份', '待清理资料', '常规备份'],
            'logs': ['工作记录', '检查报告', '其他日志', 'archive']
        })

        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'template_files': 0
        }
    
    def _load_config(self) -> Dict:
        """加载项目配置文件"""
        try:
            project_root = get_project_root()
            config_file = Path(project_root) / "docs" / "03-管理" / "project_config.yaml"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                print(f"⚠️  配置文件不存在: {config_file}")
                return {}
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            return {}

    def should_exclude(self, path: Path) -> bool:
        """判断是否应该排除某个路径"""

        # 排除特定目录
        if path.name in self.excluded_dirs:
            return True

        # 排除特定文件
        if path.is_file() and path.name in self.excluded_files:
            return True

        return False

    def should_filter_special_directory(self, relative_path: str, entry: Path) -> bool:
        """判断是否应该过滤特殊目录中的项目"""
        
        # 从配置中获取允许的子目录
        allowed_bak_dirs = set(self.special_dirs.get('bak', []))
        allowed_logs_dirs = set(self.special_dirs.get('logs', []))
        
        # 检查是否在bak/目录下
        if relative_path.startswith('bak/'):
            # 如果是bak/下的直接子项，检查是否在允许列表中
            if relative_path.count('/') == 1:  # bak/xxx 格式
                dir_name = relative_path.split('/')[-1]
                if entry.is_dir() and dir_name not in allowed_bak_dirs:
                    return True  # 过滤掉不在允许列表中的目录
                elif entry.is_file():
                    return True  # 过滤掉bak/下的所有文件
            elif relative_path.count('/') > 1:  # bak/xxx/yyy 格式
                return True  # 过滤掉bak/子目录下的所有内容
        
        # 检查是否在logs/目录下
        elif relative_path.startswith('logs/'):
            # 如果是logs/下的直接子项，检查是否在允许列表中
            if relative_path.count('/') == 1:  # logs/xxx 格式
                dir_name = relative_path.split('/')[-1]
                if entry.is_dir() and dir_name not in allowed_logs_dirs:
                    return True  # 过滤掉不在允许列表中的目录
                elif entry.is_file():
                    return True  # 过滤掉logs/下的所有文件
            elif relative_path.count('/') > 1:  # logs/xxx/yyy 格式
                return True  # 过滤掉logs/子目录下的所有内容
        
        return False

    def scan_filtered_directory(self, dir_path: Path, relative_path: str) -> List[Dict]:
        """扫描经过特殊过滤的目录（bak/和logs/）"""
        items = []
        
        # 从配置中获取允许的子目录
        if relative_path == "bak":
            allowed_dirs = set(self.special_dirs.get('bak', []))
        elif relative_path == "logs":
            allowed_dirs = set(self.special_dirs.get('logs', []))
        else:
            return items
        
        try:
            # 获取目录下所有项目
            entries = list(dir_path.iterdir())
            # 按名称排序，目录在前
            entries.sort(key=lambda x: (x.is_file(), x.name.lower()))
            
            for entry in entries:
                if self.should_exclude(entry):
                    continue
                
                # 只处理允许的目录，忽略所有文件
                if entry.is_dir() and entry.name in allowed_dirs:
                    self.stats['total_dirs'] += 1
                    item_relative_path = f"{relative_path}/{entry.name}"
                    
                    item = {
                        'type': 'directory',
                        'name': entry.name,
                        'path': item_relative_path,
                        'children': []  # 不扫描子目录内容
                    }
                    items.append(item)
        
        except PermissionError:
            print(f"⚠️  权限不足，跳过目录: {dir_path}")
        except Exception as e:
            print(f"❌ 扫描目录时出错 {dir_path}: {e}")
        
        return items

    def scan_directory(self, dir_path: Path, relative_path: str = "") -> List[Dict]:
        """扫描目录结构

        Args:
            dir_path: 要扫描的目录路径
            relative_path: 相对路径前缀

        Returns:
            目录结构列表
        """
        items = []

        try:
            # 获取目录下所有项目
            entries = list(dir_path.iterdir())
            # 按名称排序，目录在前
            entries.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for entry in entries:
                if self.should_exclude(entry):
                    continue

                # 构建相对路径
                if relative_path:
                    item_relative_path = f"{relative_path}/{entry.name}"
                else:
                    item_relative_path = entry.name

                # 特殊处理bak/和logs/目录，只显示指定的子目录名
                if self.should_filter_special_directory(item_relative_path, entry):
                    continue

                if entry.is_dir():
                    # 目录
                    self.stats['total_dirs'] += 1
                    
                    # 对于bak/和logs/目录，只扫描允许的子目录
                    children = []
                    if item_relative_path == "bak" or item_relative_path == "logs":
                        children = self.scan_filtered_directory(entry, item_relative_path)
                    else:
                        children = self.scan_directory(entry, item_relative_path)
                    
                    item = {
                        'type': 'directory',
                        'name': entry.name,
                        'path': item_relative_path,
                        'children': children
                    }
                    items.append(item)

                else:
                    # 文件
                    self.stats['total_files'] += 1
                    if self.is_template_file(entry):
                        self.stats['template_files'] += 1

                    item = {
                        'type': 'file',
                        'name': entry.name,
                        'path': item_relative_path,
                        'size': entry.stat().st_size if entry.exists() else 0
                    }
                    items.append(item)

        except PermissionError:
            print(f"⚠️  权限不足，跳过目录: {dir_path}")
        except Exception as e:
            print(f"❌ 扫描目录时出错 {dir_path}: {e}")

        return items

    def is_template_file(self, file_path: Path) -> bool:
        """判断是否为模板文件"""
        template_extensions = {'.template', '.tpl', '.tmpl', '.example'}
        return any(file_path.name.endswith(ext) for ext in template_extensions)

    def generate_markdown(self, structure: List[Dict], title: str = "项目目录结构") -> str:
        """生成Markdown格式的目录结构

        Args:
            structure: 目录结构数据
            title: 文档标题

        Returns:
            Markdown格式的字符串
        """
        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## 目录结构")
        lines.append("")
        lines.append("```")
        
        def generate_tree(items: List[Dict], prefix: str = "", is_last_list: List[bool] = None) -> None:
            """生成目录树结构"""
            if is_last_list is None:
                is_last_list = []
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                
                # 构建当前行的前缀
                current_prefix = ""
                for j, is_last_parent in enumerate(is_last_list):
                    if j == len(is_last_list) - 1:
                        continue
                    current_prefix += "│   " if not is_last_parent else "    "
                
                # 添加当前项的连接符
                if is_last_list:
                    current_prefix += "└── " if is_last else "├── "
                
                # 输出当前项
                if item['type'] == 'directory':
                    lines.append(f"{current_prefix}{item['name']}/")
                    # 递归处理子目录
                    children = item.get('children', [])
                    if children:
                        new_is_last_list = is_last_list + [is_last]
                        generate_tree(children, current_prefix, new_is_last_list)
                else:
                    lines.append(f"{current_prefix}{item['name']}")
        
        # 生成目录树
        generate_tree(structure)
        
        lines.append("```")
        lines.append("")

        # 添加统计信息
        lines.append("## 统计信息")
        lines.append("")
        lines.append(f"- **目录数量**: {self.stats['total_dirs']}")
        lines.append(f"- **文件数量**: {self.stats['total_files']}")
        lines.append(f"- **模板文件**: {self.stats['template_files']}")
        lines.append("")

        # 添加说明
        lines.append("## 说明")
        lines.append("")
        lines.append("- 此文档由目录结构更新工具自动生成")
        lines.append("- 已排除常见的临时文件和缓存目录")
        lines.append("- 模板文件包括 .template、.tpl、.tmpl、.example 等扩展名的文件")
        lines.append("- 目录路径以 / 结尾，文件路径不带结尾符号")
        lines.append("")

        return "\n".join(lines)

    def save_structure(self, structure: List[Dict], output_file: Path) -> None:
        """保存目录结构到文件

        Args:
            structure: 目录结构数据
            output_file: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 生成Markdown内容
            markdown_content = self.generate_markdown(structure)

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print("\n✅ 目录结构标准清单已生成:")
            print(f"   {output_file}")

            print("📊 统计信息:")
            print(f"   - 目录数量: {self.stats['total_dirs']}")
            print(f"   - 文件数量: {self.stats['total_files']}")
            print(f"   - 模板文件: {self.stats['template_files']}")

        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            raise


def main():
    """主函数"""
    try:
        # 获取项目根目录
        project_root_str = get_project_root()
        project_root = Path(project_root_str)
        print(f"📁 项目根目录: {project_root}")

        # 创建生成器
        generator = DirectoryStructureGenerator()

        # 扫描目录结构
        print("🔍 正在扫描目录结构...")
        structure = generator.scan_directory(project_root)

        # 生成输出文件路径
        output_file = project_root / "docs" / "01-设计" / "目录结构标准清单.md"

        # 保存结构
        generator.save_structure(structure, output_file)

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("生成完成")
    print("=" * 60)


if __name__ == "__main__":
    main()