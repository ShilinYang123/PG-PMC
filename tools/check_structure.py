# -*- coding: utf-8 -*-
"""
增强版目录结构合规性检查工具

功能：
- 详细的日志记录和错误处理
- 环境验证和路径检查
- 鲁棒的路径处理
- 问题诊断和调试信息

作者：雨俊
创建时间：2025-07-08
"""

import re
import sys
import logging
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set


class EnhancedStructureChecker:
    """增强版目录结构检查器"""

    def __init__(self, root_path: str, whitelist_file: str):
        """初始化检查器

        Args:
            root_path: 项目根目录路径
            whitelist_file: 白名单文件路径
        """
        # 设置日志记录
        self._setup_logging()

        # 验证和设置路径
        self.root_path = self._validate_and_resolve_path(root_path, "项目根目录")
        self.whitelist_file = self._validate_and_resolve_path(
            whitelist_file, "白名单文件"
        )

        self.logger.info(f"初始化检查器 - 根目录: {self.root_path}")
        self.logger.info(f"初始化检查器 - 白名单: {self.whitelist_file}")

        # 加载配置文件
        self.config = self._load_config()

        # 从配置文件中获取排除规则
        structure_config = self.config.get("structure_check", {})

        excluded_dirs_list = structure_config.get(
            "excluded_dirs",
            [
                "__pycache__",
                ".git",
                ".vscode",
                ".idea",
                "node_modules",
                ".pytest_cache",
                ".coverage",
                "htmlcov",
                "dist",
                "build",
                "*.egg-info",
                ".tox",
                ".mypy_cache",
                ".DS_Store",
                "Thumbs.db",
                ".venv",
                "venv",
                # 注意：移除"env"以避免.env文件被错误排除
            ],
        )
        # 强制移除.env以避免.env文件被错误排除
        if ".env" in excluded_dirs_list:
            excluded_dirs_list.remove(".env")
        self.excluded_dirs = set(excluded_dirs_list)

        self.excluded_files = set(
            structure_config.get(
                "excluded_files",
                [
                    ".gitkeep",
                    ".DS_Store",
                    "Thumbs.db",
                    "*.pyc",
                    "*.pyo",
                    "*.pyd",
                    "__pycache__",
                    "*.so",
                    "*.dylib",
                    "*.dll",
                ],
            )
        )

        # 允许的隐藏文件/目录
        self.allowed_hidden_items = set(
            structure_config.get(
                "allowed_hidden_items",
                [
                    ".env",
                    ".env.example",
                    ".gitignore",
                    ".dockerignore",
                    ".eslintrc.js",
                    ".prettierrc",
                    ".pre-commit-config.yaml",
                    ".devcontainer",
                    ".github",
                    ".venv",
                ],
            )
        )

        # 特殊目录配置（从配置文件中获取）
        special_dirs_config = structure_config.get(
            "special_dirs",
            {
                "bak": [
                    "github_repo",
                    "迁移备份",
                    "专项备份",
                    "待清理资料",
                    "常规备份",
                ],
                "logs": ["工作记录", "检查报告", "其他日志", "archive"],
            },
        )

        # 转换为set格式以保持兼容性
        self.special_dirs = {
            key: set(value) for key, value in special_dirs_config.items()
        }

        # 检查结果统计
        self.stats = {
            "total_dirs_expected": 0,
            "total_files_expected": 0,
            "total_dirs_actual": 0,
            "total_files_actual": 0,
            "missing_dirs": 0,
            "missing_files": 0,
            "extra_dirs": 0,
            "extra_files": 0,
            "compliance_rate": 0.0,
        }

        # 检查结果详情
        self.results = {
            "missing_items": [],
            "extra_items": [],
            "compliant_items": [],
            "errors": [],
        }

    def _load_config(self) -> Dict:
        """加载项目配置文件"""
        try:
            # 从当前脚本位置向上查找项目根目录
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            config_file = project_root / "docs" / "03-管理" / "project_config.yaml"

            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            else:
                self.logger.debug(f"配置文件不存在: {config_file}")
                return {}
        except Exception as e:
            self.logger.debug(f"加载配置文件失败: {e}")
            return {}

    def should_filter_special_directory(self, relative_path: str, entry: Path) -> bool:
        """判断是否应该过滤特殊目录中的项目（与update_structure.py保持一致）"""

        # 从配置中获取允许的子目录
        allowed_bak_dirs = self.special_dirs.get("bak", set())
        allowed_logs_dirs = self.special_dirs.get("logs", set())

        # 检查是否在bak/目录下
        if relative_path.startswith("bak/"):
            # 如果是bak/下的直接子项，检查是否在允许列表中
            if relative_path.count("/") == 1:  # bak/xxx 格式
                dir_name = relative_path.split("/")[-1]
                if entry.is_dir() and dir_name not in allowed_bak_dirs:
                    return True  # 过滤掉不在允许列表中的目录
                elif entry.is_file():
                    return True  # 过滤掉bak/下的所有文件
            elif relative_path.count("/") > 1:  # bak/xxx/yyy 格式
                return True  # 过滤掉bak/子目录下的所有内容

        # 检查是否在logs/目录下
        elif relative_path.startswith("logs/"):
            # 如果是logs/下的直接子项，检查是否在允许列表中
            if relative_path.count("/") == 1:  # logs/xxx 格式
                dir_name = relative_path.split("/")[-1]
                if entry.is_dir() and dir_name not in allowed_logs_dirs:
                    return True  # 过滤掉不在允许列表中的目录
                elif entry.is_file():
                    return True  # 过滤掉logs/下的所有文件
            elif relative_path.count("/") > 1:  # logs/xxx/yyy 格式
                return True  # 过滤掉logs/子目录下的所有内容

        return False
    
    def _is_valid_directory_name(self, dir_name: str) -> bool:
        """验证目录名称是否符合规范
        
        遵循规范与流程.md第八章命名规范
        
        Args:
            dir_name: 目录名称
            
        Returns:
            True 如果名称符合规范，False 否则
        """
        if not dir_name or not dir_name.strip():
            return False
            
        # 检查是否包含非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in dir_name for char in illegal_chars):
            return False
            
        # 检查长度限制
        if len(dir_name) > 255:
            return False
            
        return True
    
    def _validate_structure_compliance(self, structure: Dict[str, Set[str]]) -> bool:
        """验证结构是否符合项目规范要求
        
        遵循规范与流程.md第七章目录文件及清单管理规定
        
        Args:
            structure: 目录结构数据
            
        Returns:
            True 如果符合规范，False 否则
        """
        try:
            # 检查核心目录是否存在
            required_dirs = {'docs', 'project', 'tools'}
            existing_dirs = structure.get('directories', set())
            
            missing_core_dirs = required_dirs - existing_dirs
            if missing_core_dirs:
                self.logger.error(f"缺少核心目录: {missing_core_dirs}")
                return False
                
            # 检查特殊目录结构
            if 'bak' in existing_dirs:
                bak_subdirs = {d for d in existing_dirs if d.startswith('bak/')}
                required_bak_subdirs = {'bak/github_repo', 'bak/迁移备份', 'bak/专项备份', 'bak/待清理资料', 'bak/常规备份'}
                if bak_subdirs and not bak_subdirs.issuperset(required_bak_subdirs):
                    self.logger.warning(f"bak目录结构不完整: 期望 {required_bak_subdirs}, 实际 {bak_subdirs}")
                    
            if 'logs' in existing_dirs:
                logs_subdirs = {d for d in existing_dirs if d.startswith('logs/')}
                required_logs_subdirs = {'logs/工作记录', 'logs/检查报告', 'logs/其他日志', 'logs/archive'}
                if logs_subdirs and not logs_subdirs.issuperset(required_logs_subdirs):
                    self.logger.warning(f"logs目录结构不完整: 期望 {required_logs_subdirs}, 实际 {logs_subdirs}")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"结构合规性验证失败: {e}")
            return False



    def _setup_logging(self):
        """设置日志记录"""
        # 创建日志目录 - 确保在项目根目录内
        try:
            from tools.config_loader import ConfigLoader

            config_loader = ConfigLoader()
            project_root = config_loader.get_project_root()
        except Exception:
            # 备用方案：使用当前工作目录作为项目根目录
            project_root = Path.cwd()

        log_dir = project_root / "logs" / "检查报告"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 设置日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"enhanced_check_debug_{timestamp}.log"

        # 配置日志记录器
        self.logger = logging.getLogger("enhanced_checker")
        self.logger.setLevel(logging.DEBUG)

        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器 - 只显示警告和错误信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 清理7天前的debug日志文件（遵守规范与流程.md中的清理策略）
        self._cleanup_old_debug_logs(log_dir)
        
        self.logger.info(f"日志记录已启用，日志文件: {log_file}")

    def _cleanup_old_debug_logs(self, log_dir: Path) -> None:
        """清理7天前的debug日志文件（遵守规范与流程.md中的清理策略）
        
        Args:
            log_dir: 日志目录路径
        """
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=7)
            
            # 查找所有debug日志文件
            debug_log_pattern = "enhanced_check_debug_*.log"
            debug_logs = list(log_dir.glob(debug_log_pattern))
            
            cleaned_count = 0
            for log_file in debug_logs:
                try:
                    # 获取文件修改时间
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    # 如果文件超过7天，则删除
                    if file_mtime < cutoff_time:
                        log_file.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"已清理过期debug日志: {log_file.name}")
                        
                except Exception as e:
                    self.logger.warning(f"清理日志文件失败 {log_file.name}: {e}")
                    
            if cleaned_count > 0:
                self.logger.info(f"已清理 {cleaned_count} 个过期debug日志文件")
                
        except Exception as e:
            self.logger.warning(f"debug日志清理过程出错: {e}")

    def _validate_and_resolve_path(self, path_str: str, description: str) -> Path:
        """验证并解析路径

        Args:
            path_str: 路径字符串
            description: 路径描述

        Returns:
            解析后的Path对象

        Raises:
            FileNotFoundError: 如果路径不存在
        """
        try:
            path = Path(path_str)

            # 尝试解析为绝对路径
            if not path.is_absolute():
                # 相对路径，相对于脚本目录解析
                script_dir = Path(__file__).parent
                path = (script_dir / path).resolve()
            else:
                path = path.resolve()

            # 检查路径是否存在
            if not path.exists():
                raise FileNotFoundError(f"{description}不存在: {path}")

            self.logger.debug(f"路径验证成功 - {description}: {path}")
            return path

        except Exception as e:
            error_msg = f"路径验证失败 - {description} ({path_str}): {e}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

    def verify_environment(self) -> bool:
        """验证运行环境

        Returns:
            True 如果环境正常，False 否则
        """
        self.logger.info("开始环境验证...")

        try:
            # 检查Python版本
            python_version = sys.version
            self.logger.info(f"Python版本: {python_version}")

            # 检查当前工作目录
            cwd = Path.cwd()
            self.logger.info(f"当前工作目录: {cwd}")

            # 检查脚本目录
            script_dir = Path(__file__).parent
            self.logger.info(f"脚本目录: {script_dir}")

            # 检查项目根目录的关键子目录
            required_dirs = ["docs", "tools"]
            for dir_name in required_dirs:
                dir_path = self.root_path / dir_name
                if not dir_path.exists():
                    self.logger.warning(f"缺少关键目录: {dir_path}")
                    return False
                else:
                    self.logger.debug(f"关键目录存在: {dir_path}")

            # 检查白名单文件的可读性
            try:
                with open(self.whitelist_file, "r", encoding="utf-8") as f:
                    content_preview = f.read(200)
                    self.logger.debug(f"白名单文件预览: {content_preview[:100]}...")
            except Exception as e:
                self.logger.error(f"无法读取白名单文件: {e}")
                return False

            # 检查输出目录的写权限
            output_dir = self.root_path / "logs" / "检查报告"
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                test_file = output_dir / "test_write_permission.tmp"
                test_file.write_text("test", encoding="utf-8")
                test_file.unlink()
                self.logger.debug(f"输出目录写权限正常: {output_dir}")
            except Exception as e:
                self.logger.error(f"输出目录写权限检查失败: {e}")
                return False

            self.logger.info("✅ 环境验证通过")
            return True

        except Exception as e:
            self.logger.error(f"环境验证失败: {e}")
            return False

    def should_exclude_path(self, path: Path) -> bool:
        """判断路径是否应该被排除（与update_structure.py保持一致）

        Args:
            path: 要检查的路径

        Returns:
            True 如果应该排除，False 否则
        """
        # 排除隐藏目录和文件（除了特定的配置文件）
        if path.name.startswith(".") and path.name not in {
            ".env",
            ".env.local",
            ".env.production",
            ".env.template",
            ".env.example",
            ".gitignore",
            ".dockerignore",
            ".eslintrc.js",
            ".prettierrc",
            ".pre-commit-config.yaml",
            ".devcontainer",
            ".github",
            ".venv",
            ".cache",
            ".coverage",
            ".pytest_cache",
            ".vscode",
        }:
            self.logger.debug(f"排除隐藏路径: {path}")
            return True

        # 排除特定目录
        if path.name in self.excluded_dirs:
            self.logger.debug(f"排除特定目录: {path} (名称: {path.name}, 是否为目录: {path.is_dir()}, excluded_dirs: {self.excluded_dirs})")
            return True

        # 排除特定文件
        if path.is_file() and path.name in self.excluded_files:
            self.logger.debug(f"排除特定文件: {path}")
            return True

        return False

    def _scan_directory_recursive(
        self, current_path: Path, relative_path: str = ""
    ) -> Dict[str, Set[str]]:
        """递归扫描目录结构（与update_structure.py保持一致）

        Args:
            current_path: 当前扫描的绝对路径
            relative_path: 相对于根目录的路径

        Returns:
            包含目录和文件集合的字典
        """
        structure = {"directories": set(), "files": set()}

        try:
            if not current_path.exists():
                self.logger.warning(f"路径不存在: {current_path}")
                return structure

            if not current_path.is_dir():
                self.logger.warning(f"不是目录: {current_path}")
                return structure

            self.logger.debug(f"扫描目录: {current_path} (相对路径: {relative_path})")

            # 获取目录内容
            try:
                items = list(current_path.iterdir())
                self.logger.debug(f"目录 {current_path} 包含 {len(items)} 个项目")
            except PermissionError as e:
                self.logger.error(f"权限错误，无法访问目录 {current_path}: {e}")
                return structure
            except Exception as e:
                self.logger.error(f"读取目录失败 {current_path}: {e}")
                return structure

            for item in items:
                try:
                    # 跳过应该排除的路径
                    if self.should_exclude_path(item):
                        continue

                    # 构建相对路径
                    if relative_path:
                        item_relative_path = f"{relative_path}/{item.name}"
                    else:
                        item_relative_path = item.name

                    if item.is_dir():
                        # 添加目录
                        structure["directories"].add(item_relative_path)
                        self.logger.debug(f"添加目录: {item_relative_path}")

                        # 对于bak和logs目录，使用与update_structure.py
                        # 相同的过滤逻辑
                        if item_relative_path == "bak" or item_relative_path == "logs":
                            # 只扫描允许的子目录，不扫描其内容
                            allowed_dirs = {
                                "bak": {
                                    "github_repo",
                                    "迁移备份",
                                    "专项备份",
                                    "待清理资料",
                                    "常规备份",
                                },
                                "logs": {"工作记录", "检查报告", "其他日志", "archive"},
                            }.get(item_relative_path, set())

                            try:
                                # 获取目录下所有项目
                                entries = list(item.iterdir())
                                # 按名称排序，目录在前
                                entries.sort(
                                    key=lambda x: (
                                        x.is_file(),
                                        x.name.lower(),
                                    )
                                )

                                for entry in entries:
                                    if self.should_exclude_path(entry):
                                        continue

                                    # 只处理允许的目录，忽略所有文件
                                    if entry.is_dir() and entry.name in allowed_dirs:
                                        subdir_relative = (
                                            f"{item_relative_path}/" f"{entry.name}"
                                        )
                                        structure["directories"].add(subdir_relative)
                                        self.logger.debug(
                                            f"添加特殊目录: {subdir_relative}"
                                        )
                                        # 不扫描子目录内容，与update_structure.py保持一致

                            except PermissionError:
                                self.logger.warning(f"权限不足，跳过目录: {item}")
                            except Exception as e:
                                self.logger.error(f"扫描目录时出错 {item}: {e}")
                        else:
                            # 普通目录，递归扫描
                            sub_structure = self._scan_directory_recursive(
                                item, item_relative_path
                            )
                            structure["directories"].update(
                                sub_structure["directories"]
                            )
                            structure["files"].update(sub_structure["files"])

                    elif item.is_file():
                        # 添加文件
                        structure["files"].add(item_relative_path)
                        self.logger.debug(f"添加文件: {item_relative_path}")

                except Exception as e:
                    self.logger.error(f"处理项目失败 {item}: {e}")
                    continue

            return structure

        except Exception as e:
            self.logger.error(f"扫描目录失败 {current_path}: {e}")
            return structure

    def scan_current_structure(self) -> Dict[str, Set[str]]:
        """扫描当前项目目录结构

        Returns:
            当前目录结构
        """
        self.logger.info(f"开始扫描当前目录结构: {self.root_path}")

        try:
            structure = self._scan_directory_recursive(self.root_path)

            # 更新统计信息
            self.stats["total_dirs_actual"] = len(structure["directories"])
            self.stats["total_files_actual"] = len(structure["files"])

            self.logger.info(
                f"扫描完成 - 目录: {
                    self.stats['total_dirs_actual']} 个, 文件: {
                    self.stats['total_files_actual']} 个"
            )

            # 记录前10个目录和文件作为样本
            sample_dirs = list(sorted(structure["directories"]))[:10]
            sample_files = list(sorted(structure["files"]))[:10]

            self.logger.debug(f"目录样本: {sample_dirs}")
            self.logger.debug(f"文件样本: {sample_files}")

            return structure

        except Exception as e:
            error_msg = f"扫描当前结构失败: {e}"
            self.logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return {"directories": set(), "files": set()}

    def parse_whitelist(self) -> Dict[str, Set[str]]:
        """解析白名单文件（目录结构标准清单.md）

        Returns:
            标准目录结构
        """
        self.logger.info(f"开始解析白名单文件: {self.whitelist_file}")

        structure = {"directories": set(), "files": set()}

        try:
            with open(self.whitelist_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.logger.debug(f"白名单文件大小: {len(content)} 字符")

            # 查找目录树部分
            tree_pattern = r"```[\s\S]*?```"
            tree_matches = re.findall(tree_pattern, content)

            if not tree_matches:
                raise ValueError("未找到目录树结构")

            self.logger.debug(f"找到 {len(tree_matches)} 个代码块")

            # 处理每个代码块
            for i, tree_block in enumerate(tree_matches):
                self.logger.debug(f"处理代码块 {i + 1}/{len(tree_matches)}")

                # 移除代码块标记
                tree_lines = tree_block.strip("`").strip().split("\n")

                # 跳过空行，保留树结构行和顶级目录行
                tree_lines = [
                    line
                    for line in tree_lines
                    if line.strip()
                    and (
                        ("├──" in line or "└──" in line or "│" in line)
                        or (
                            line.strip().endswith("/")
                            and not line.startswith(" ")
                            and not line.startswith("\t")
                        )
                    )
                ]

                if not tree_lines:
                    continue

                self.logger.debug(f"代码块 {i + 1} 包含 {len(tree_lines)} 行树结构")

                # 解析树结构
                path_stack = []
                current_top_level = None

                for line_num, line in enumerate(tree_lines, 1):
                    try:
                        self.logger.debug(f"解析行 {line_num}: '{line.strip()}'")

                        # 检查是否是顶级目录（没有树形符号且没有缩进的行）
                        if (
                            line.strip().endswith("/")
                            and not any(
                                symbol in line for symbol in ["├──", "└──", "│"]
                            )
                            and not line.startswith(" ")
                            and not line.startswith("\t")
                        ):
                            # 顶级目录
                            dir_name = line.strip()[:-1]
                            if dir_name:
                                structure["directories"].add(dir_name)
                                current_top_level = dir_name
                                path_stack = [dir_name]  # 重置路径栈
                            continue

                        # 如果没有当前顶级目录，跳过
                        if not current_top_level:
                            self.logger.debug(f"跳过行（无顶级目录）: {line.strip()}")
                            continue

                        depth = self._calculate_depth(line)
                        name = self._extract_name_from_line(line)

                        self.logger.debug(f"深度: {depth}, 名称: '{name}'")

                        if not name:
                            self.logger.debug(f"跳过行（无名称）: {line.strip()}")
                            continue

                        # 调整路径栈深度（保留顶级目录）
                        while len(path_stack) > depth:
                            path_stack.pop()

                        # 确保路径栈至少包含顶级目录
                        if not path_stack:
                            path_stack = [current_top_level]

                        # 构建完整路径
                        full_path = "/".join(path_stack + [name])

                        # 判断是目录还是文件
                        if line.rstrip().endswith("/"):
                            # 目录
                            structure["directories"].add(full_path.rstrip("/"))
                            path_stack.append(name.rstrip("/"))
                            self.logger.debug(f"添加标准目录: {full_path.rstrip('/')}")
                        else:
                            # 文件
                            structure["files"].add(full_path)
                            self.logger.debug(f"添加标准文件: {full_path}")

                    except Exception as e:
                        self.logger.warning(
                            f"解析第 {line_num} 行失败: {line.strip()} - {e}"
                        )
                        continue

            # 更新统计信息
            self.stats["total_dirs_expected"] = len(structure["directories"])
            self.stats["total_files_expected"] = len(structure["files"])

            self.logger.info(
                f"白名单解析完成 - 标准目录: {
                    self.stats['total_dirs_expected']} 个, 标准文件: {
                    self.stats['total_files_expected']} 个"
            )

            # 记录前10个目录和文件作为样本
            sample_dirs = list(sorted(structure["directories"]))[:10]
            sample_files = list(sorted(structure["files"]))[:10]

            self.logger.debug(f"标准目录样本: {sample_dirs}")
            self.logger.debug(f"标准文件样本: {sample_files}")

            if not structure["directories"] and not structure["files"]:
                raise ValueError("未解析到任何标准结构")

            return structure

        except Exception as e:
            error_msg = f"解析白名单文件失败: {e}"
            self.logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return {"directories": set(), "files": set()}

    def _calculate_depth(self, line: str) -> int:
        """计算目录树中行的深度（与原始工具保持一致）

        Args:
            line: 目录树中的一行

        Returns:
            深度级别
        """
        # 移除行首空白，计算缩进
        stripped = line.lstrip()
        if not stripped:
            return 0

        # 对于树形结构，分析不同的行类型：
        # 深度0: 根目录，如 "bak/", "docs/" (没有树形符号)
        # 深度1: ├── github_repo/ 或 └── 迁移备份/ (有一个 ├── 或 └──)
        # 深度2: │   ├── 01-设计/ (有一个 │ 和一个 ├──)
        # 深度3: │   │   ├── 文件名 (有两个 │ 和一个 ├──)

        if any(symbol in line for symbol in ["├──", "└──"]):
            # 包含树形符号的行
            tree_symbol_pos = max(line.find("├──"), line.find("└──"))

            # 计算深度：从行首到树形符号位置，每4个字符为一个深度级别
            # 这包括了│字符和空格的组合
            depth = (tree_symbol_pos // 4) + 1

            return depth
        elif line.strip().startswith("│"):
            # 纯粹的连接线，不是文件或目录
            return 0
        elif stripped.endswith("/") and not any(
            symbol in line for symbol in ["├──", "└──", "│"]
        ):
            # 根目录，如 "bak/", "docs/"
            return 0
        else:
            # 普通缩进，每4个空格为一个深度级别
            indent = len(line) - len(stripped)
            return indent // 4

    def _extract_name_from_line(self, line: str) -> str:
        """从目录树行中提取名称

        Args:
            line: 目录树中的一行

        Returns:
            提取的名称
        """
        # 移除树字符，提取文件/目录名
        name = re.sub(r"^[\s│├└─]*", "", line).strip()
        return name

    def compare_structures(
        self, whitelist: Dict[str, Set[str]], current: Dict[str, Set[str]]
    ):
        """对比标准结构和当前结构

        Args:
            whitelist: 标准结构
            current: 当前结构
        """
        self.logger.info("开始对比结构差异")

        try:
            # 查找缺失的目录
            missing_dirs = whitelist["directories"] - current["directories"]
            for dir_path in missing_dirs:
                self.results["missing_items"].append(
                    {"type": "directory", "path": dir_path}
                )
                self.logger.debug(f"缺失目录: {dir_path}")

            # 查找缺失的文件
            missing_files = whitelist["files"] - current["files"]
            for file_path in missing_files:
                self.results["missing_items"].append(
                    {"type": "file", "path": file_path}
                )
                self.logger.debug(f"缺失文件: {file_path}")

            # 查找多余的目录
            extra_dirs = current["directories"] - whitelist["directories"]
            for dir_path in extra_dirs:
                self.results["extra_items"].append(
                    {"type": "directory", "path": dir_path}
                )
                self.logger.debug(f"多余目录: {dir_path}")

            # 查找多余的文件
            extra_files = current["files"] - whitelist["files"]
            for file_path in extra_files:
                self.results["extra_items"].append({"type": "file", "path": file_path})
                self.logger.debug(f"多余文件: {file_path}")

            # 查找符合的项目
            compliant_dirs = whitelist["directories"] & current["directories"]
            compliant_files = whitelist["files"] & current["files"]

            for dir_path in compliant_dirs:
                self.results["compliant_items"].append(
                    {"type": "directory", "path": dir_path}
                )

            for file_path in compliant_files:
                self.results["compliant_items"].append(
                    {"type": "file", "path": file_path}
                )

            # 更新统计信息
            self.stats["missing_dirs"] = len(missing_dirs)
            self.stats["missing_files"] = len(missing_files)
            self.stats["extra_dirs"] = len(extra_dirs)
            self.stats["extra_files"] = len(extra_files)

            # 计算合规率 - 考虑多余项目的影响
            total_expected = (
                self.stats["total_dirs_expected"] + self.stats["total_files_expected"]
            )
            total_compliant = len(compliant_dirs) + len(compliant_files)
            total_extra = len(extra_dirs) + len(extra_files)

            if total_expected > 0:
                # 合规分数 = 合规项目数 - 多余项目数
                compliance_score = total_compliant - total_extra
                self.stats["compliance_rate"] = max(
                    0.0, (compliance_score / total_expected) * 100
                )
            else:
                self.stats["compliance_rate"] = 0.0

            self.logger.info(f"对比完成 - 合规率: {self.stats['compliance_rate']:.1f}%")
            self.logger.info(f"缺失项目: {len(missing_dirs) + len(missing_files)} 个")
            self.logger.info(f"多余项目: {len(extra_dirs) + len(extra_files)} 个")

        except Exception as e:
            error_msg = f"结构对比失败: {e}"
            self.logger.error(error_msg)
            self.results["errors"].append(error_msg)

    def run_enhanced_check(self) -> str:
        """运行增强版检查

        Returns:
            检查报告内容
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始增强版目录结构合规性检查")
            self.logger.info("=" * 60)

            # 1. 环境验证
            if not self.verify_environment():
                raise RuntimeError("环境验证失败，无法继续检查")

            # 2. 解析白名单
            self.logger.info("步骤 1/4: 解析白名单文件")
            whitelist_structure = self.parse_whitelist()
            if (
                not whitelist_structure["directories"]
                and not whitelist_structure["files"]
            ):
                raise ValueError("白名单文件解析失败或为空")

            # 3. 扫描当前结构
            self.logger.info("步骤 2/4: 扫描当前目录结构")
            current_structure = self.scan_current_structure()

            # 4. 对比结构
            self.logger.info("步骤 3/4: 对比分析结构差异")
            self.compare_structures(whitelist_structure, current_structure)

            # 5. 生成报告
            self.logger.info("步骤 4/4: 生成检查报告")
            report = self.generate_enhanced_report()

            self.logger.info("✅ 增强版检查完成")
            return report

        except Exception as e:
            error_msg = f"增强版检查过程中发生错误: {e}"
            self.logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return self.generate_enhanced_report()

    def generate_enhanced_report(self) -> str:
        """生成增强版检查报告

        Returns:
            报告内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 计算合规状态
        if self.stats["compliance_rate"] >= 95:
            status = "优秀"
            status_icon = "✅"
        elif self.stats["compliance_rate"] >= 80:
            status = "良好"
            status_icon = "⚠️"
        else:
            status = "需要改进"
            status_icon = "[X]"

        report_lines = [
            "# 增强版目录结构合规性检查报告",
            "",
            f"**生成时间**: {timestamp}",
            f"**项目路径**: `{
                self.root_path}`",
            f"**白名单文件**: `{
                self.whitelist_file}`",
            "",
            "## 检查概要",
            "",
            f"{status_icon} **合规状态**: {status}",
            f"📊 **整体合规率**: {
                self.stats['compliance_rate']:.1f}%",
            "",
            "### 统计信息",
            "",
            "| 项目类型 | 标准数量 | 实际数量 | 缺失数量 | 多余数量 |",
            "|----------|----------|----------|----------|----------|",
            f"| 目录 | {
                self.stats['total_dirs_expected']} | {
                self.stats['total_dirs_actual']} | {
                self.stats['missing_dirs']} | {
                self.stats['extra_dirs']} |",
            f"| 文件 | {
                self.stats['total_files_expected']} | {
                self.stats['total_files_actual']} | {
                self.stats['missing_files']} | {
                self.stats['extra_files']} |",
            "",
        ]

        # 添加错误信息
        if self.results["errors"]:
            report_lines.extend(["## ⚠️ 检查过程中的错误", ""])
            for i, error in enumerate(self.results["errors"], 1):
                report_lines.append(f"{i}. {error}")
            report_lines.append("")

        # 添加缺失项目
        if self.results["missing_items"]:
            report_lines.extend(["## 📋 缺失项目", ""])
            for item in sorted(self.results["missing_items"], key=lambda x: x["path"]):
                item_type = "📁" if item["type"] == "directory" else "📄"
                report_lines.append(f"- {item_type} `{item['path']}`")
            report_lines.append("")

        # 添加多余项目
        if self.results["extra_items"]:
            report_lines.extend(["## 🗑️ 多余项目", ""])
            for item in sorted(self.results["extra_items"], key=lambda x: x["path"]):
                item_type = "📁" if item["type"] == "directory" else "📄"
                report_lines.append(f"- {item_type} `{item['path']}`")
            report_lines.append("")

        # 添加诊断信息
        report_lines.extend(
            [
                "## 🔍 诊断信息",
                "",
                f"- **Python版本**: {sys.version.split()[0]}",
                f"- **当前工作目录**: `{Path.cwd()}`",
                f"- **脚本目录**: `{Path(__file__).parent}`",
                "- **日志文件**: 查看 `logs/检查报告/enhanced_check_debug_*.log`",
                "",
            ]
        )

        # 添加建议
        if self.stats["compliance_rate"] < 100:
            report_lines.extend(["## 💡 整改建议", ""])

            if self.results["missing_items"]:
                report_lines.append("### 缺失项目处理")
                report_lines.append("1. 检查是否为必要的目录或文件")
                report_lines.append("2. 创建缺失的目录结构")
                report_lines.append("3. 添加必要的配置文件")
                report_lines.append("")

            if self.results["extra_items"]:
                report_lines.append("### 多余项目处理")
                report_lines.append("1. 确认是否为临时文件或测试文件")
                report_lines.append("2. 删除或移动到适当位置")
                report_lines.append("3. 如果是新增的必要文件，更新标准清单")
                report_lines.append("")

        report_lines.extend(["---", "", "*报告由增强版目录结构检查工具生成*"])

        return "\n".join(report_lines)


def main():
    """主函数
    
    严格遵循规范与流程.md第五章工作结束事项中的目录结构合规性检查要求
    按照第七章目录文件及清单管理规定执行标准化检查流程
    """
    print("\n🔍 启动目录结构合规性检查")
    print("📋 遵循《规范与流程.md》第七章目录文件及清单管理规定")
    
    # 标准化路径配置（遵循第十章开发环境规范）
    try:
        # 获取项目根目录和白名单文件路径
        script_dir = Path(__file__).parent
        root_dir = script_dir.parent
        whitelist_file = root_dir / "docs" / "01-设计" / "目录结构标准清单.md"
        print(f"✅ 配置加载成功，项目根目录: {root_dir}")
    except Exception as e:
        print(f"⚠️  配置加载失败，使用默认路径: {e}")
        root_dir = Path.cwd()
        whitelist_file = (
            root_dir / "docs" / "01-设计" / "目录结构标准清单.md"
        )
        print(f"📁 使用默认项目根目录: {root_dir}")

    # 验证关键文件存在性（遵循第二章文件权限管理规范）
    if not whitelist_file.exists():
        print(f"❌ 标准清单文件不存在: {whitelist_file}")
        print("💡 请确保《目录结构标准清单.md》文件存在于正确位置")
        sys.exit(3)

    # 创建检查器实例（标准化初始化）
    try:
        checker = EnhancedStructureChecker(
            root_path=str(root_dir), 
            whitelist_file=str(whitelist_file)
        )
        print("✅ 检查器初始化成功")
    except Exception as e:
        print(f"❌ 检查器初始化失败: {e}")
        sys.exit(4)

    # 执行标准化检查流程
    print("\n🔄 开始执行结构合规性检查...")
    try:
        report_content = checker.run_enhanced_check()
        print("✅ 检查执行完成")
    except Exception as e:
        print(f"❌ 检查执行失败: {e}")
        sys.exit(5)

    # 生成标准化报告（遵循第五章工作结束事项要求）
    try:
        # 生成报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"增强版检查报告_{timestamp}.md"
        report_file = root_dir / "logs" / "检查报告" / report_filename

        # 确保输出目录存在
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入报告文件
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"\n📋 检查报告已生成: {report_file}")
    except Exception as e:
        print(f"\n❌ 报告生成异常: {e}")

    # 输出标准化统计信息（遵循第八章命名规范）
    compliance_rate = checker.stats.get("compliance_rate", 0)
    missing_items = checker.results.get("missing_items", [])
    extra_items = checker.results.get("extra_items", [])
    
    print(f"\n📊 检查统计信息:")
    print(f"   📁 目录数量: {checker.stats['total_dirs_actual']} (标准: {checker.stats['total_dirs_expected']})")
    print(f"   📄 文件数量: {checker.stats['total_files_actual']} (标准: {checker.stats['total_files_expected']})")
    print(f"   ✅ 合规率: {compliance_rate:.1f}%")
    print(f"   ❌ 缺失数量: {len(missing_items)}")
    print(f"   ⚠️  多余数量: {len(extra_items)}")

    # 输出违规项清单（标准化格式）
    if missing_items:
        print(f"\n❌ 缺失项目清单 (共{len(missing_items)}项)：")
        for i, item in enumerate(sorted(missing_items, key=lambda x: x["path"])[:10], 1):
            item_type = "📁" if item["type"] == "directory" else "📄"
            print(f"   {i:2d}. {item_type} {item['path']}")
        if len(missing_items) > 10:
            print(f"   ... 还有 {len(missing_items) - 10} 个缺失项目")

    if extra_items:
        print(f"\n⚠️  多余项目清单 (共{len(extra_items)}项)：")
        for i, item in enumerate(sorted(extra_items, key=lambda x: x["path"])[:10], 1):
            item_type = "📁" if item["type"] == "directory" else "📄"
            print(f"   {i:2d}. {item_type} {item['path']}")
        if len(extra_items) > 10:
            print(f"   ... 还有 {len(extra_items) - 10} 个多余项目")

    # 标准化合规性评估（遵循项目质量标准）
    print(f"\n📈 合规性评估:")
    if compliance_rate >= 98:
        status = "优秀"
        icon = "🏆"
        exit_code = 0
    elif compliance_rate >= 95:
        status = "良好"
        icon = "✅"
        exit_code = 0
    elif compliance_rate >= 90:
        status = "合格"
        icon = "⚠️"
        exit_code = 1
    elif compliance_rate >= 80:
        status = "需要改进"
        icon = "🔧"
        exit_code = 1
    else:
        status = "不合格"
        icon = "❌"
        exit_code = 2
    
    print(f"   {icon} 项目结构合规状态: {status} ({compliance_rate:.1f}%)")
    
    # 提供改进建议（遵循规范要求）
    if compliance_rate < 100:
        print(f"\n💡 改进建议:")
        if missing_items:
            print(f"   • 补充缺失的 {len(missing_items)} 个项目")
        if extra_items:
            print(f"   • 清理多余的 {len(extra_items)} 个项目")
        print(f"   • 参考《规范与流程.md》第七章进行整改")
        print(f"   • 使用update_structure.py更新标准清单")
    
    print(f"\n🎯 检查完成，退出码: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
