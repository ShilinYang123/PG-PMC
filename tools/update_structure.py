#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构标准清单生成工具

功能：
- 扫描项目根目录，生成完整的目录结构标准清单
- 按照规范要求，排除 bak 和 logs 目录的具体文件内容
- 生成符合标准格式的 Markdown 文档

作者：雨俊
创建时间：2025-06-24
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class DirectoryStructureGenerator:
    """目录结构生成器"""
    
    def __init__(self, root_path: str):
        """初始化生成器
        
        Args:
            root_path: 项目根目录路径
        """
        self.root_path = Path(root_path).resolve()
        self.excluded_dirs = {'.git', '__pycache__', 'node_modules'}
        self.excluded_files = {'.DS_Store', 'Thumbs.db', '*.pyc'}
        
        # 对于特殊目录（bak、logs），只保留子目录结构，
        # 不扫描具体文件内容
        self.special_dirs = {'bak', 'logs'}
        
        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'template_files': 0
        }
    
    def should_exclude_path(self, path: Path, parent_name: str = None) -> bool:
        """判断路径是否应该被排除
        
        Args:
            path: 要检查的路径
            parent_name: 父目录名称
            
        Returns:
            True 如果应该排除，False 否则
        """
        # 排除隐藏目录和文件（除了特定的配置文件）
        if (path.name.startswith('.') and
            path.name not in {'.env', '.env.example', '.gitignore',
                              '.dockerignore', '.eslintrc.js',
                              '.prettierrc', '.pre-commit-config.yaml'}):
            return True
            
        # 排除特定目录
        if path.name in self.excluded_dirs:
            return True
            
        # 排除特定文件
        if path.is_file() and path.name in self.excluded_files:
            return True
            
        return False
    
    def scan_directory(self, dir_path: Path, relative_path: str = "") -> List[Dict]:
        """扫描目录结构
        
        Args:
            dir_path: 要扫描的目录路径
            relative_path: 相对路径
            
        Returns:
            目录结构列表
        """
        items = []
        
        try:
            # 获取目录中的所有项目
            entries = sorted(dir_path.iterdir(),
                          key=lambda x: (x.is_file(), x.name.lower()))
            
            for entry in entries:
                if self.should_exclude_path(entry):
                    continue
                    
                rel_path = str(entry.relative_to(self.root_path)) \
                    .replace('\\', '/')
                
                if entry.is_dir():
                    self.stats['total_dirs'] += 1
                    
                    # 处理特殊目录（bak和logs）
                    if entry.name in self.special_dirs:
                        # 扫描所有子目录，但不扫描子目录内容
                        subdirs = []
                        
                        try:
                            for subentry in sorted(entry.iterdir(), key=lambda x: x.name.lower()):
                                if subentry.is_dir() and not self.should_exclude_path(subentry):
                                    self.stats['total_dirs'] += 1  # 统计子目录
                                    subdirs.append({
                                        'name': subentry.name,
                                        'type': 'directory',
                                        'path': os.path.join(rel_path, subentry.name),
                                        'children': []  # 不扫描子目录内容
                                    })
                        except PermissionError:
                            pass
                        
                        items.append({
                            'name': entry.name,
                            'type': 'directory',
                            'path': rel_path,
                            'children': subdirs
                        })
                    else:
                        # 普通目录，递归扫描
                        children = self.scan_directory(entry, rel_path)
                        items.append({
                            'name': entry.name,
                            'type': 'directory',
                            'path': rel_path,
                            'children': children
                        })
                        
                elif entry.is_file():
                    self.stats['total_files'] += 1
                    
                    # 统计模板文件
                    if any(keyword in entry.name.lower()
                           for keyword in ['template', 'example',
                                           'sample', '.template']):
                        self.stats['template_files'] += 1
                    
                    items.append({
                        'name': entry.name,
                        'type': 'file',
                        'path': rel_path
                    })
                    
        except PermissionError:
            print(f"警告: 无法访问目录 {dir_path}")
            
        return items
    
    def generate_tree_text(self, items: List[Dict], prefix: str = "",
                           is_last: bool = True) -> str:
        """生成树形文本结构
        
        Args:
            items: 目录项目列表
            prefix: 前缀字符串
            is_last: 是否是最后一个项目
            
        Returns:
            树形文本字符串
        """
        result = []
        
        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            # 确定连接符
            connector = "└── " if is_last_item else "├── "
            
            # 添加目录或文件名
            if item['type'] == 'directory':
                result.append(f"{prefix}{connector}{item['name']}/")
                
                # 递归处理子项目
                if item.get('children'):
                    child_prefix = prefix + ("    " if is_last_item else "│   ")
                    child_tree = self.generate_tree_text(
                        item['children'], child_prefix, is_last_item
                    )
                    result.append(child_tree)
            else:
                result.append(f"{prefix}{connector}{item['name']}")
        
        return "\n".join(filter(None, result))
    
    def generate_markdown(self, structure: List[Dict]) -> str:
        """生成 Markdown 格式的目录结构文档
        
        Args:
            structure: 目录结构数据
            
        Returns:
            Markdown 格式的文档内容
        """
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成树形结构
        tree_text = self.generate_tree_text(structure)
        
        markdown_content = f"""# 目录结构标准清单

> 生成时间: {timestamp}
> 生成工具: update_structure.py
> 目录数量: {self.stats['total_dirs']}
> 文件数量: {self.stats['total_files']}
> 模板文件: {self.stats['template_files']}


## 当前目录结构

### 完整目录树

```
{self.root_path.name}/
{tree_text}
```

## 说明

### 目录结构规范

1. **bak目录**: 仅显示标准子目录结构，不包含具体备份文件
   - `github_repo/`: Git仓库备份
   - `专项备份/`: 专项功能备份
   - `迁移备份/`: 项目迁移备份
   - `待清理资料/`: 待处理的临时文件
   - `常规备份/`: 日常备份文件

2. **logs目录**: 仅显示标准子目录结构，不包含具体日志文件
   - `archive/`: 归档日志
   - `其他日志/`: 其他类型日志
   - `工作记录/`: 工作过程记录
   - `检查报告/`: 各类检查报告

3. **docs目录**: 项目文档，包含所有设计、开发、管理和模板文档

4. **project目录**: 项目源代码，包含完整的应用程序代码

5. **tools目录**: 项目工具脚本，包含各种辅助开发工具

### 统计信息

- 总目录数: {self.stats['total_dirs']}
- 总文件数: {self.stats['total_files']}
- 模板文件数: {self.stats['template_files']}
- 生成时间: {timestamp}

---

*此文档由 update_structure.py 自动生成，请勿手动编辑*
"""
        
        return markdown_content
    
    def generate_structure_list(self) -> str:
        """生成目录结构标准清单
        
        Returns:
            Markdown 格式的目录结构清单
        """
        print(f"开始扫描目录: {self.root_path}")

        # 扫描目录结构
        structure = self.scan_directory(self.root_path)

        # 生成 Markdown 文档
        markdown_content = self.generate_markdown(structure)

        print(f"扫描完成: 目录 {self.stats['total_dirs']} 个，文件 {self.stats['total_files']} 个")

        return markdown_content


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    print("=" * 60)
    print("目录结构标准清单生成工具")
    print("=" * 60)
    print(f"项目根目录: {root_dir}")

    try:
        # 创建生成器实例
        generator = DirectoryStructureGenerator(str(root_dir))

        # 生成目录结构清单
        markdown_content = generator.generate_structure_list()

        # 输出文件路径
        output_file = root_dir / "docs" / "01-设计" / "目录结构标准清单.md"

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"\n✅ 目录结构标准清单已生成:")
        print(f"   {output_file}")
        print("📊 统计信息:")
        print(f"   - 目录数量: {generator.stats['total_dirs']}")
        print(f"   - 文件数量: {generator.stats['total_files']}")
        print(f"   - 模板文件: {generator.stats['template_files']}")

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("生成完成")
    print("=" * 60)


if __name__ == "__main__":
    main()