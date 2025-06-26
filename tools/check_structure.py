#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构合规性检查工具

功能：
- 读取目录结构标准清单（白名单）
- 扫描当前项目目录结构
- 对比分析，生成合规性检查报告
- 识别多余文件、缺失文件和不合规目录

作者：雨俊
创建时间：2025-06-24
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set


class StructureChecker:
    """目录结构检查器"""

    def __init__(self, root_path: str, whitelist_file: str):
        """初始化检查器

        Args:
            root_path: 项目根目录路径
            whitelist_file: 白名单文件路径
        """
        self.root_path = Path(root_path).resolve()
        self.whitelist_file = Path(whitelist_file).resolve()

        # 排除规则（与update_structure.py保持一致）
        self.excluded_dirs = {'.git', '__pycache__', 'node_modules'}
        self.excluded_files = {'.DS_Store', 'Thumbs.db', '*.pyc'}

        # 特殊目录（bak和logs只检查子目录结构）
        self.special_dirs = {
            'bak': {'github_repo', '专项备份', '迁移备份', '待清理资料', '常规备份'},
            'logs': {'archive', '其他日志', '工作记录', '检查报告'}
        }

        # 检查结果统计
        self.stats = {
            'total_dirs_expected': 0,
            'total_files_expected': 0,
            'total_dirs_actual': 0,
            'total_files_actual': 0,
            'missing_dirs': 0,
            'missing_files': 0,
            'extra_dirs': 0,
            'extra_files': 0,
            'compliance_rate': 0.0
        }

        # 检查结果详情
        self.results = {
            'missing_items': [],
            'extra_items': [],
            'compliant_items': [],
            'errors': []
        }

    def should_exclude_path(self, path: Path) -> bool:
        """判断路径是否应该被排除（与update_structure.py保持一致）

        Args:
            path: 要检查的路径

        Returns:
            True 如果应该排除，False 否则
        """
        # 排除隐藏目录和文件（除了特定的配置文件）
        if path.name.startswith('.') and path.name not in {
            '.env', '.env.example', '.gitignore', '.dockerignore',
            '.eslintrc.js', '.prettierrc', '.pre-commit-config.yaml'
        }:
            return True

        # 排除特定目录
        if path.name in self.excluded_dirs:
            return True

        # 排除特定文件
        if path.is_file() and path.name in self.excluded_files:
            return True

        return False

    def _scan_directory_recursive(self, dir_path: Path,
                                  structure: Dict[str, Set[str]],
                                  relative_path: str = "") -> None:
        """递归扫描目录结构（与update_structure.py保持一致）

        Args:
            dir_path: 要扫描的目录路径
            structure: 存储结构的字典
            relative_path: 相对路径
        """
        try:
            # 获取目录中的所有项目
            entries = sorted(dir_path.iterdir(),
                             key=lambda x: (x.is_file(), x.name.lower()))

            for entry in entries:
                if self.should_exclude_path(entry):
                    continue

                rel_path = ((relative_path + '/' + entry.name)
                            if relative_path else entry.name)
                if entry.is_dir():
                    # 处理特殊目录（bak和logs）
                    if entry.name in self.special_dirs:
                        # 添加特殊目录本身
                        structure['directories'].add(rel_path)
                        
                        # 只添加允许的子目录（与update_structure.py保持一致）
                        allowed_subdirs = self.special_dirs[entry.name]
                        for subdir_name in allowed_subdirs:
                            subdir_path = entry / subdir_name
                            if subdir_path.exists() and subdir_path.is_dir():
                                subdir_rel_path = rel_path + '/' + subdir_name
                                structure['directories'].add(subdir_rel_path)
                                # 不递归扫描特殊目录的子目录内容
                    else:
                        # 普通目录，添加并递归扫描
                        structure['directories'].add(rel_path)
                        self._scan_directory_recursive(entry, structure,
                                                       rel_path)

                elif entry.is_file():
                    structure['files'].add(rel_path)

        except PermissionError:
            print("警告: 无法访问目录 {}".format(dir_path))

    def parse_whitelist(self) -> Dict[str, Set[str]]:
        """解析白名单文件，提取标准目录结构

        Returns:
            包含目录和文件路径的字典
        """
        whitelist_structure = {
            'directories': set(),
            'files': set()
        }

        try:
            with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否是章节标题
                if line == "### 目录":
                    current_section = "directories"
                    continue
                elif line == "### 文件":
                    current_section = "files"
                    continue
                elif line.startswith("#") or line.startswith("##"):
                    current_section = None
                    continue
                    
                # 解析列表项
                if line.startswith("- ") and current_section:
                    path = line[2:].strip()  # 移除 "- " 前缀
                    
                    if current_section == "directories":
                        # 目录路径，移除末尾的 /
                        if path.endswith("/"):
                            path = path[:-1]
                        if path:  # 非空路径才添加
                            whitelist_structure['directories'].add(path)
                    elif current_section == "files":
                        # 文件路径
                        if path:  # 非空路径才添加
                            whitelist_structure['files'].add(path)

            # 更新统计信息
            dirs_count = len(whitelist_structure['directories'])
            self.stats['total_dirs_expected'] = dirs_count
            self.stats['total_files_expected'] = len(
                whitelist_structure['files'])

            print("✅ 白名单解析完成")
            print("   - 目录: {} 个".format(self.stats['total_dirs_expected']))
            print("   - 文件: {} 个".format(self.stats['total_files_expected']))

            return whitelist_structure

        except Exception as e:
            error_msg = "解析白名单文件失败: {}".format(e)
            self.results['errors'].append(error_msg)
            print("❌ {}".format(error_msg))
            return whitelist_structure

    def scan_current_structure(self) -> Dict[str, Set[str]]:
        """扫描当前目录结构

        Returns:
            包含当前目录和文件路径的字典
        """
        current_structure = {
            'directories': set(),
            'files': set()
        }

        try:
            # 使用类似update_structure.py的扫描逻辑
            self._scan_directory_recursive(self.root_path, current_structure)

            # 移除根目录自身
            current_structure['directories'].discard('')

            # 更新统计信息
            self.stats['total_dirs_actual'] = len(
                current_structure['directories'])
            self.stats['total_files_actual'] = len(current_structure['files'])

            print("✅ 当前结构扫描完成")
            print("   - 目录: {} 个".format(self.stats['total_dirs_actual']))
            print("   - 文件: {} 个".format(self.stats['total_files_actual']))

            return current_structure

        except Exception as e:
            error_msg = "扫描当前目录结构失败: {}".format(e)
            self.results['errors'].append(error_msg)
            print("❌ {}".format(error_msg))
            return current_structure

    def compare_structures(self, whitelist: Dict[str, Set[str]],
                           current: Dict[str, Set[str]]) -> None:
        """对比目录结构

        Args:
            whitelist: 白名单结构
            current: 当前结构
        """
        # 查找缺失项目
        missing_dirs = whitelist['directories'] - current['directories']
        missing_files = whitelist['files'] - current['files']

        # 查找多余项目
        extra_dirs = current['directories'] - whitelist['directories']
        extra_files = current['files'] - whitelist['files']

        # 查找符合规范的项目
        compliant_dirs = whitelist['directories'] & current['directories']
        compliant_files = whitelist['files'] & current['files']

        # 更新结果
        for item in missing_dirs:
            self.results['missing_items'].append(('目录', item))
        for item in missing_files:
            self.results['missing_items'].append(('文件', item))
        for item in extra_dirs:
            self.results['extra_items'].append(('目录', item))
        for item in extra_files:
            self.results['extra_items'].append(('文件', item))
        for item in compliant_dirs:
            self.results['compliant_items'].append(('目录', item))
        for item in compliant_files:
            self.results['compliant_items'].append(('文件', item))

        # 更新统计信息
        self.stats['missing_dirs'] = len(missing_dirs)
        self.stats['missing_files'] = len(missing_files)
        self.stats['extra_dirs'] = len(extra_dirs)
        self.stats['extra_files'] = len(extra_files)

        # 计算合规率
        total_expected = (self.stats['total_dirs_expected'] +
                          self.stats['total_files_expected'])
        total_compliant = len(compliant_dirs) + len(compliant_files)
        if total_expected > 0:
            self.stats['compliance_rate'] = (
                total_compliant / total_expected) * 100
        else:
            self.stats['compliance_rate'] = 100.0

        print("✅ 结构对比完成")
        print("   - 合规率: {:.1f}%".format(self.stats['compliance_rate']))
        missing_total = len(missing_dirs) + len(missing_files)
        print("   - 缺失项目: {} 个".format(missing_total))
        print("   - 多余项目: {} 个".format(len(extra_dirs) + len(extra_files)))

    def generate_report(self) -> str:
        """生成检查报告

        Returns:
            Markdown格式的检查报告
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 确定合规状态
        if self.stats['compliance_rate'] >= 95:
            status = "✅ 优秀"
            status_desc = "目录结构高度符合规范要求"
        elif self.stats['compliance_rate'] >= 85:
            status = "🟡 良好"
            status_desc = "目录结构基本符合规范，有少量问题"
        elif self.stats['compliance_rate'] >= 70:
            status = "🟠 一般"
            status_desc = "目录结构存在一些问题，需要改进"
        else:
            status = "❌ 较差"
            status_desc = "目录结构存在严重问题，需要立即整改"

        # 生成报告内容
        report = "# 目录结构检查报告\n\n"
        report += "> 检查时间: {}\n".format(timestamp)
        report += "> 检查工具: check_structure.py\n"
        report += "> 项目路径: {}\n".format(self.root_path)
        report += "> 白名单文件: {}\n\n".format(self.whitelist_file.name)

        report += "## 检查结果概览\n\n"
        report += "### 合规状态: {}\n\n".format(status)
        report += "{}\n\n".format(status_desc)

        # 统计信息表格
        report += "### 统计信息\n\n"
        report += "| 项目 | 预期数量 | 实际数量 | 差异 |\n"
        report += "|------|----------|----------|------|\n"
        dirs_diff = (self.stats['total_dirs_actual'] -
                     self.stats['total_dirs_expected'])
        dirs_diff_str = ("+{}".format(dirs_diff) if dirs_diff > 0
                         else str(dirs_diff))
        report += "| 目录 | {} | {} | {} |\n".format(
            self.stats['total_dirs_expected'],
            self.stats['total_dirs_actual'],
            dirs_diff_str
        )
        files_diff = (self.stats['total_files_actual'] -
                      self.stats['total_files_expected'])
        files_diff_str = ("+{}".format(files_diff) if files_diff > 0
                          else str(files_diff))
        report += "| 文件 | {} | {} | {} |\n\n".format(
            self.stats['total_files_expected'],
            self.stats['total_files_actual'],
            files_diff_str
        )

        # 问题统计表格
        report += "### 问题统计\n\n"
        report += "| 问题类型 | 数量 |\n"
        report += "|----------|------|\n"
        report += "| 缺失目录 | {} |\n".format(self.stats['missing_dirs'])
        report += "| 缺失文件 | {} |\n".format(self.stats['missing_files'])
        report += "| 多余目录 | {} |\n".format(self.stats['extra_dirs'])
        report += "| 多余文件 | {} |\n\n".format(
            self.stats['extra_files'])

        report += "**整体合规率: {:.1f}%**\n\n".format(
            self.stats['compliance_rate'])

        # 详细问题列表
        if self.results['missing_items']:
            report += "## 缺失项目\n\n"
            for item_type, item_path in sorted(self.results['missing_items']):
                report += "- {} `{}`\n".format(item_type, item_path)
            report += "\n"

        if self.results['extra_items']:
            report += "## 多余项目\n\n"
            for item_type, item_path in sorted(self.results['extra_items']):
                report += "- {} `{}`\n".format(item_type, item_path)
            report += "\n"

        # 错误信息
        if self.results['errors']:
            report += "## 检查过程中的错误\n\n"
            for error in self.results['errors']:
                report += "- ❌ {}\n".format(error)
            report += "\n"

        # 整改建议
        report += "## 整改建议\n\n"

        if self.stats['missing_dirs'] > 0 or self.stats['missing_files'] > 0:
            report += "### 缺失项目处理\n\n"
            report += "1. 检查缺失的目录和文件是否确实需要\n"
            report += "2. 如果需要，请按照标准清单创建相应的目录和文件\n"
            report += "3. 如果不需要，请更新标准清单\n\n"

        if self.stats['extra_dirs'] > 0 or self.stats['extra_files'] > 0:
            report += "### 多余项目处理\n\n"
            report += "1. 检查多余的目录和文件是否为临时文件或测试文件\n"
            report += "2. 如果是临时文件，建议删除或移动到适当位置\n"
            report += "3. 如果是新增的必要文件，请更新标准清单\n\n"

        if self.stats['compliance_rate'] >= 95:
            report += "### 维护建议\n\n"
            report += "目录结构已经很规范，请继续保持：\n"
            report += "1. 定期运行结构检查\n"
            report += "2. 新增文件时遵循现有规范\n"
            report += "3. 及时更新标准清单\n\n"

        report += "---\n\n"
        report += "*此报告由 check_structure.py 自动生成*\n"

        return report

    def run_check(self) -> str:
        """执行完整的检查流程

        Returns:
            检查报告内容
        """
        try:
            print("开始目录结构合规性检查...")
            print("项目路径: {}".format(self.root_path))
            print("白名单文件: {}".format(self.whitelist_file))
            print("-" * 60)

            # 1. 解析白名单
            whitelist_structure = self.parse_whitelist()
            if (not whitelist_structure['directories'] and
                    not whitelist_structure['files']):
                raise ValueError("白名单文件解析失败或为空")

            # 2. 扫描当前结构
            current_structure = self.scan_current_structure()

            # 3. 对比结构
            self.compare_structures(whitelist_structure, current_structure)

            # 4. 生成报告
            report = self.generate_report()

            return report

        except Exception as e:
            error_msg = "检查过程中发生错误: {}".format(e)
            self.results['errors'].append(error_msg)
            print("❌ {}".format(error_msg))
            return self.generate_report()


def main():
    """主函数"""
    # 获取项目根目录和白名单文件路径
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    whitelist_file = root_dir / "docs" / "01-设计" / "目录结构标准清单.md"

    # 检查白名单文件是否存在
    if not whitelist_file.exists():
        print("❌ 白名单文件不存在: {}".format(whitelist_file))
        print("请先运行 update_structure.py 生成标准清单")
        sys.exit(1)

    try:
        # 创建检查器实例
        checker = StructureChecker(str(root_dir), str(whitelist_file))

        # 执行检查
        report_content = checker.run_check()

        # 生成报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = "目录结构检查报告_{}.md".format(timestamp)
        report_file = root_dir / "logs" / "检查报告" / report_filename

        # 确保输出目录存在
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入报告文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 输出结果
        print("\n✅ 检查报告已生成:")
        print("   {}".format(report_file))
        print("📊 检查结果:")
        print("   - 合规率: {:.1f}%".format(checker.stats['compliance_rate']))
        missing_count = (checker.stats['missing_dirs'] +
                         checker.stats['missing_files'])
        print("   - 缺失项目: {} 个".format(missing_count))
        extra_count = (checker.stats['extra_dirs'] +
                       checker.stats['extra_files'])
        print("   - 多余项目: {} 个".format(extra_count))

        if checker.results['errors']:
            print("   - 错误数量: {} 个".format(len(checker.results['errors'])))

        # 根据合规率设置退出码
        if checker.stats['compliance_rate'] < 70:
            print("\n⚠️  目录结构存在严重问题，建议立即整改")
            sys.exit(2)
        elif checker.stats['compliance_rate'] < 95:
            print("\n⚠️  目录结构存在一些问题，建议及时处理")
            sys.exit(1)
        else:
            print("\n✅ 目录结构符合规范要求")
            sys.exit(0)

    except Exception as e:
        print("❌ 检查失败: {}".format(e))
        sys.exit(1)

    finally:
        print("\n" + "=" * 60)
        print("检查完成")
        print("=" * 60)


if __name__ == "__main__":
    main()
