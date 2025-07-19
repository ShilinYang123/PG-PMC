# -*- coding: utf-8 -*-
"""
报告生成器模块
提供统一的报告生成功能，支持多种格式输出
"""

import sys
from pathlib import Path
from typing import Set, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from tools.config_loader import ConfigLoader
except ImportError:
    # 如果无法导入，使用默认配置
    class ConfigLoader:
        @staticmethod
        def load_config():
            return {}


class ReportGenerator:
    """报告生成器类"""

    def __init__(self):
        """初始化报告生成器"""
        self.config = ConfigLoader.load_config()

    def generate_directory_tree(self, paths: Set[str], max_depth: int = 3) -> str:
        """生成目录树结构"""
        if not paths:
            return "(空目录)"

        # 将路径转换为Path对象并排序
        path_objects = [Path(p) for p in paths]
        path_objects.sort()

        # 构建树结构
        tree_lines = []
        processed_dirs = set()

        for path_obj in path_objects:
            # 获取相对于项目根目录的路径
            try:
                rel_path = path_obj.relative_to(project_root)
            except ValueError:
                rel_path = path_obj

            parts = rel_path.parts
            if len(parts) > max_depth:
                continue

            # 构建每一级的缩进
            for i, part in enumerate(parts):
                current_path = Path(*parts[: i + 1])
                if current_path not in processed_dirs:
                    indent = "│   " * i
                    if i == len(parts) - 1:
                        # 最后一级，判断是文件还是目录
                        if path_obj.is_dir():
                            tree_lines.append(f"{indent}├── {part}/")
                        else:
                            tree_lines.append(f"{indent}├── {part}")
                    else:
                        tree_lines.append(f"{indent}├── {part}/")
                    processed_dirs.add(current_path)

        return "\n".join(tree_lines)

    def format_file_list(self, files: List[Path], title: str = "文件列表") -> str:
        """格式化文件列表"""
        if not files:
            return f"## {title}\n\n(无文件)\n\n"

        content = f"## {title}\n\n"
        for file_path in sorted(files):
            try:
                rel_path = file_path.relative_to(project_root)
                content += f"- {rel_path}\n"
            except ValueError:
                content += f"- {file_path}\n"

        return content + "\n"

    def format_directory_list(
        self, directories: List[Path], title: str = "目录列表"
    ) -> str:
        """格式化目录列表"""
        if not directories:
            return f"## {title}\n\n(无目录)\n\n"

        content = f"## {title}\n\n"
        for dir_path in sorted(directories):
            try:
                rel_path = dir_path.relative_to(project_root)
                content += f"- {rel_path}/\n"
            except ValueError:
                content += f"- {dir_path}/\n"

        return content + "\n"

    def save_report(
        self, content: str, output_file: Path, message: str = "报告已保存"
    ) -> None:
        """保存报告到文件"""
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            self._print_file_link(message, output_file)

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            raise

    def _print_file_link(self, message: str, file_path: Optional[Path] = None) -> str:
        """打印可点击的文件链接"""
        if file_path:
            # 在终端中显示可点击的文件链接
            clickable_link = f"file:///{file_path.as_posix()}"
            return f"{message}: {clickable_link}"
        return message

    def generate_standard_report_header(
        self,
        tool_name: str,
        directories_count: int,
        files_count: int,
        template_files_count: int = 0,
    ) -> str:
        """生成标准报告头部"""
        # 从配置文件读取时间戳格式
        structure_config = self.config.get("structure_check", {})
        reporting_config = structure_config.get("reporting", {})
        timestamp_format = reporting_config.get("timestamp_format", "%Y-%m-%d %H:%M:%S")

        timestamp = datetime.now().strftime(timestamp_format)

        header = (
            f"# 目录结构标准清单\n\n"
            f"> 生成时间: {timestamp}\n"
            f"> 生成工具: {tool_name}\n"
            f"> 目录数量: {directories_count}\n"
            f"> 文件数量: {files_count}\n"
        )

        if template_files_count > 0:
            header += f"> 模板文件: {template_files_count}\n"

        header += "\n\n"
        return header

    def _generate_header(
        self, tool_name: str, whitelist_count: int, actual_count: int, result: str
    ) -> str:
        """生成检查报告头部"""
        # 从配置文件读取时间戳格式
        structure_config = self.config.get("structure_check", {})
        reporting_config = structure_config.get("reporting", {})
        timestamp_format = reporting_config.get("timestamp_format", "%Y-%m-%d %H:%M:%S")

        timestamp = datetime.now().strftime(timestamp_format)

        return (
            f"# 目录结构检查报告\n\n"
            f"> 检查时间: {timestamp}\n"
            f"> 检查工具: {tool_name}\n"
            f"> 白名单项目: {whitelist_count}\n"
            f"> 实际项目: {actual_count}\n"
            f"> 检查结果: {result}\n\n"
        )

    def generate_directory_section(
        self, paths: Set[str], title: str = "完整目录树"
    ) -> str:
        """生成目录结构部分"""
        tree_content = self.generate_directory_tree(paths)

        # 从配置文件读取目录树根节点名称
        structure_config = self.config.get("structure_check", {})
        reporting_config = structure_config.get("reporting", {})
        tree_config = reporting_config.get("tree_display", {})
        root_name = tree_config.get("root_name", "PinGao/")

        return (
            f"## 当前目录结构\n\n"
            f"```\n"
            f"{root_name}\n"
            f"{tree_content}\n"
            f"```\n\n"
        )

    def print_file_link(self, message: str, file_path: Path) -> None:
        """打印文件链接到控制台"""
        # 将Windows路径转换为URL格式
        file_url = f"file:///{str(file_path).replace(chr(92), '/')}"
        # 将消息和文件路径分行显示，避免行太长导致链接被截断
        print(f"{message}:")
        print(f"  {file_url}")
        # 不再记录到日志，避免重复输出
        # logger.info(f"{message}: {str(file_path)}")
