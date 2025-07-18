#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置迁移工具

本模块提供配置迁移功能，将项目中分散的配置文件整合到统一配置管理中心。

主要功能：
1. 扫描现有配置文件
2. 迁移分散的配置
3. 统一配置格式
4. 验证迁移结果
5. 生成迁移报告

作者: 雨俊
创建时间: 2025-01-10
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import dotenv_values

try:
    from core.config_center import ConfigCenter, get_config_center
    from core.unified_logging import get_logger
except ImportError:
    # 简单的logger替代
    class SimpleLogger:
        def error(self, msg):
            print(f"ERROR: {msg}")

        def info(self, msg):
            print(f"INFO: {msg}")

        def warning(self, msg):
            print(f"WARNING: {msg}")

        def debug(self, msg):
            print(f"DEBUG: {msg}")

    def get_logger(name):
        return SimpleLogger()

    # 如果无法导入，则跳过这些功能
    ConfigCenter = None
    get_config_center = None


class ConfigMigration:
    """配置迁移工具

    负责将项目中分散的配置文件整合到统一配置管理中心。
    """

    def __init__(self, project_root: Optional[Path] = None):
        """初始化配置迁移工具

        Args:
            project_root: 项目根目录路径
        """
        self.logger = get_logger(self.__class__.__name__)

        # 初始化配置中心
        self.config_center = get_config_center(project_root)
        self.project_root = self.config_center.paths.project_root

        # 迁移状态
        self.migration_report: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "status": "pending",
            "scanned_files": [],
            "migrated_configs": [],
            "errors": [],
            "warnings": [],
            "summary": {},
        }

        self.logger.info(f"配置迁移工具已初始化，项目根目录: {self.project_root}")

    def scan_existing_configs(self) -> List[Dict[str, Any]]:
        """扫描现有配置文件

        Returns:
            List[Dict[str, Any]]: 发现的配置文件列表
        """
        self.logger.info("开始扫描现有配置文件")

        config_files = []

        # 定义要扫描的配置文件模式
        config_patterns = [
            # YAML配置文件
            "**/*.yaml",
            "**/*.yml",
            # JSON配置文件
            "**/*.json",
            # 环境变量文件
            "**/.env*",
            # Python配置文件
            "**/config.py",
            "**/settings.py",
            "**/config_*.py",
            # 其他配置文件
            "**/project_config.*",
        ]

        # 排除的目录
        exclude_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "env",
            "build",
            "dist",
            ".tox",
            "backups",
            "logs",
            "temp",
            "uploads",
        }

        try:
            for pattern in config_patterns:
                for file_path in self.project_root.rglob(pattern):
                    # 跳过排除的目录
                    if any(
                        exclude_dir in file_path.parts for exclude_dir in exclude_dirs
                    ):
                        continue

                    # 跳过非文件
                    if not file_path.is_file():
                        continue

                    # 分析配置文件
                    config_info = self._analyze_config_file(file_path)
                    if config_info:
                        config_files.append(config_info)
                        self.migration_report["scanned_files"].append(str(file_path))

            self.logger.info(f"✅ 扫描完成，发现 {len(config_files)} 个配置文件")
            return config_files

        except Exception as e:
            error_msg = f"扫描配置文件失败: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.migration_report["errors"].append(error_msg)
            return []

    def migrate_configs(self, dry_run: bool = False) -> bool:
        """迁移配置文件

        Args:
            dry_run: 是否为试运行（不实际修改文件）

        Returns:
            bool: 迁移是否成功
        """
        self.migration_report["start_time"] = datetime.now().isoformat()
        self.migration_report["status"] = "running"

        try:
            self.logger.info(f"开始配置迁移 {'(试运行)' if dry_run else ''}")

            # 1. 扫描现有配置
            config_files = self.scan_existing_configs()
            if not config_files:
                self.logger.warning("未发现需要迁移的配置文件")
                return True

            # 2. 备份现有配置
            if not dry_run:
                backup_success = self._backup_existing_configs(config_files)
                if not backup_success:
                    self.logger.error("备份现有配置失败，迁移中止")
                    return False

            # 3. 加载和合并配置
            merged_config = self._merge_configs(config_files)
            if not merged_config:
                self.logger.error("合并配置失败")
                return False

            # 4. 验证合并后的配置
            validation_errors = self.config_center._validate_config(merged_config)
            if validation_errors:
                self.logger.warning(f"配置验证发现 {len(validation_errors)} 个问题")
                for error in validation_errors:
                    self.migration_report["warnings"].append(error)

            # 5. 保存新配置
            if not dry_run:
                save_success = self._save_migrated_config(merged_config)
                if not save_success:
                    self.logger.error("保存迁移配置失败")
                    return False

            # 6. 更新配置引用
            if not dry_run:
                update_success = self._update_config_references()
                if not update_success:
                    self.logger.warning("更新配置引用时出现问题")

            # 7. 生成迁移报告
            self._generate_migration_summary(merged_config, config_files)

            self.migration_report["status"] = "completed"
            self.logger.info(f"✅ 配置迁移完成 {'(试运行)' if dry_run else ''}")

            return True

        except Exception as e:
            error_msg = f"配置迁移失败: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.migration_report["errors"].append(error_msg)
            self.migration_report["status"] = "failed"
            return False

        finally:
            self.migration_report["end_time"] = datetime.now().isoformat()

    def generate_migration_report(self, output_path: Optional[Path] = None) -> Path:
        """生成迁移报告

        Args:
            output_path: 报告输出路径

        Returns:
            Path: 报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                self.project_root / "docs" / f"config_migration_report_{timestamp}.md"
            )

        try:
            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 生成报告内容
            report_content = self._generate_report_content()

            # 保存报告
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            self.logger.info(f"✅ 迁移报告已生成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"❌ 生成迁移报告失败: {e}")
            return output_path

    def _analyze_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """分析配置文件

        Args:
            file_path: 配置文件路径

        Returns:
            Optional[Dict[str, Any]]: 配置文件信息
        """
        try:
            file_info = {
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.project_root)),
                "type": self._detect_config_type(file_path),
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "content": None,
                "config_keys": [],
                "errors": [],
            }

            # 尝试加载配置内容
            content = self._load_config_content(file_path)
            if content is not None:
                file_info["content"] = content
                file_info["config_keys"] = self._extract_config_keys(content)

            return file_info

        except Exception as e:
            self.logger.warning(f"分析配置文件失败 {file_path}: {e}")
            return None

    def _detect_config_type(self, file_path: Path) -> str:
        """检测配置文件类型

        Args:
            file_path: 文件路径

        Returns:
            str: 配置文件类型
        """
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        if suffix in [".yaml", ".yml"]:
            return "yaml"
        elif suffix == ".json":
            return "json"
        elif name.startswith(".env"):
            return "env"
        elif suffix == ".py" and ("config" in name or "settings" in name):
            return "python"
        else:
            return "unknown"

    def _load_config_content(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载配置文件内容

        Args:
            file_path: 文件路径

        Returns:
            Optional[Dict[str, Any]]: 配置内容
        """
        try:
            config_type = self._detect_config_type(file_path)

            if config_type == "yaml":
                with open(file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}

            elif config_type == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            elif config_type == "env":
                return dict(dotenv_values(file_path))

            elif config_type == "python":
                # 对于Python配置文件，只提取简单的变量赋值
                return self._extract_python_config(file_path)

            return None

        except Exception as e:
            self.logger.warning(f"加载配置内容失败 {file_path}: {e}")
            return None

    def _extract_python_config(self, file_path: Path) -> Dict[str, Any]:
        """提取Python配置文件中的配置

        Args:
            file_path: Python文件路径

        Returns:
            Dict[str, Any]: 提取的配置
        """
        config = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单的正则匹配提取变量赋值
            import re

            # 匹配简单的变量赋值
            patterns = [
                r'^([A-Z_][A-Z0-9_]*)\s*=\s*["\']([^"\']*)["\'\s]*$',  # 字符串
                r"^([A-Z_][A-Z0-9_]*)\s*=\s*(\d+)\s*$",  # 整数
                r"^([A-Z_][A-Z0-9_]*)\s*=\s*(True|False)\s*$",  # 布尔值
            ]

            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("#") or not line:
                    continue

                for pattern in patterns:
                    match = re.match(pattern, line, re.MULTILINE)
                    if match:
                        key = match.group(1)
                        value = match.group(2)

                        # 类型转换
                        if value.isdigit():
                            value = int(value)
                        elif value in ["True", "False"]:
                            value = value == "True"

                        config[key] = value
                        break

            return config

        except Exception as e:
            self.logger.warning(f"提取Python配置失败 {file_path}: {e}")
            return {}

    def _extract_config_keys(
        self, content: Dict[str, Any], prefix: str = ""
    ) -> List[str]:
        """提取配置键列表

        Args:
            content: 配置内容
            prefix: 键前缀

        Returns:
            List[str]: 配置键列表
        """
        keys = []

        if not isinstance(content, dict):
            return keys

        for key, value in content.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)

            if isinstance(value, dict):
                keys.extend(self._extract_config_keys(value, full_key))

        return keys

    def _backup_existing_configs(self, config_files: List[Dict[str, Any]]) -> bool:
        """备份现有配置文件

        Args:
            config_files: 配置文件列表

        Returns:
            bool: 备份是否成功
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = (
                self.config_center.paths.backup_dir / f"migration_backup_{timestamp}"
            )
            backup_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"备份现有配置到: {backup_dir}")

            for config_file in config_files:
                source_path = Path(config_file["path"])
                relative_path = config_file["relative_path"]

                # 创建备份文件路径
                backup_file_path = backup_dir / relative_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(source_path, backup_file_path)

                self.logger.debug(f"已备份: {relative_path}")

            # 保存备份信息
            backup_info = {
                "timestamp": timestamp,
                "backup_dir": str(backup_dir),
                "files": [cf["relative_path"] for cf in config_files],
            }

            backup_info_path = backup_dir / "backup_info.json"
            with open(backup_info_path, "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ 配置备份完成，共备份 {len(config_files)} 个文件")
            return True

        except Exception as e:
            self.logger.error(f"❌ 备份配置失败: {e}")
            return False

    def _merge_configs(
        self, config_files: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """合并配置文件

        Args:
            config_files: 配置文件列表

        Returns:
            Optional[Dict[str, Any]]: 合并后的配置
        """
        try:
            self.logger.info("开始合并配置文件")

            # 从默认配置开始
            merged_config = self.config_center._get_default_config()

            # 定义配置文件优先级
            priority_order = [
                "default.yaml",
                "settings.yaml",
                "config.yaml",
                "project_config.yaml",
                ".env",
                "user_settings.yaml",
                ".env.local",
            ]

            # 按优先级排序配置文件
            sorted_configs = sorted(
                config_files, key=lambda x: self._get_config_priority(x, priority_order)
            )

            # 逐个合并配置
            for config_file in sorted_configs:
                if config_file["content"]:
                    self.logger.debug(f"合并配置: {config_file['relative_path']}")

                    # 转换配置格式
                    normalized_config = self._normalize_config_structure(config_file)

                    if normalized_config:
                        merged_config = self.config_center._deep_merge_dict(
                            merged_config, normalized_config
                        )

                        self.migration_report["migrated_configs"].append(
                            {
                                "file": config_file["relative_path"],
                                "keys_count": len(config_file["config_keys"]),
                                "type": config_file["type"],
                            }
                        )

            self.logger.info(f"✅ 配置合并完成，共处理 {len(config_files)} 个文件")
            return merged_config

        except Exception as e:
            self.logger.error(f"❌ 合并配置失败: {e}")
            return None

    def _get_config_priority(
        self, config_file: Dict[str, Any], priority_order: List[str]
    ) -> int:
        """获取配置文件优先级

        Args:
            config_file: 配置文件信息
            priority_order: 优先级顺序

        Returns:
            int: 优先级（数字越小优先级越高）
        """
        file_name = Path(config_file["path"]).name

        for i, priority_name in enumerate(priority_order):
            if priority_name in file_name:
                return i

        return len(priority_order)  # 未匹配的文件放在最后

    def _normalize_config_structure(
        self, config_file: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """规范化配置结构

        Args:
            config_file: 配置文件信息

        Returns:
            Optional[Dict[str, Any]]: 规范化后的配置
        """
        try:
            content = config_file["content"]
            config_type = config_file["type"]

            if config_type == "env":
                # 环境变量需要映射到配置结构
                return self._map_env_to_config(content)

            elif config_type in ["yaml", "json"]:
                # YAML和JSON配置直接使用
                return content

            elif config_type == "python":
                # Python配置需要映射
                return self._map_python_to_config(content)

            return content

        except Exception as e:
            self.logger.warning(f"规范化配置结构失败 {config_file['path']}: {e}")
            return None

    def _map_env_to_config(self, env_content: Dict[str, str]) -> Dict[str, Any]:
        """将环境变量映射到配置结构

        Args:
            env_content: 环境变量内容

        Returns:
            Dict[str, Any]: 映射后的配置
        """
        config = {}

        # 环境变量到配置路径的映射
        env_mappings = {
            "APP_NAME": "app.name",
            "APP_VERSION": "app.version",
            "DEBUG": "app.debug",
            "LOG_LEVEL": "app.log_level",
            "ENVIRONMENT": "app.environment",
            "SERVER_HOST": "server.host",
            "SERVER_PORT": "server.port",
            "WORKERS": "server.workers",
            "OPENAI_API_KEY": "ai.openai.api_key",
            "OPENAI_MODEL": "ai.openai.model",
            "OPENAI_MAX_TOKENS": "ai.openai.max_tokens",
            "ANTHROPIC_API_KEY": "ai.anthropic.api_key",
            "ANTHROPIC_MODEL": "ai.anthropic.model",
            "CREO_INSTALL_PATH": "creo.install_path",
            "CREO_TIMEOUT": "creo.connection_timeout",
            "DATABASE_TYPE": "database.type",
            "DATABASE_PATH": "database.sqlite.path",
            "DATABASE_URL": "database.postgresql.url",
            "TEMP_DIR": "storage.temp_dir",
            "UPLOAD_DIR": "storage.upload_dir",
            "MAX_FILE_SIZE": "storage.max_file_size",
            "LOG_FILE": "logging.file",
            "SESSION_TIMEOUT": "security.session_timeout",
        }

        for env_key, env_value in env_content.items():
            if env_key in env_mappings:
                config_path = env_mappings[env_key]

                # 类型转换
                converted_value = self._convert_env_value(env_key, env_value)

                # 设置配置值
                self._set_nested_config(config, config_path, converted_value)

        return config

    def _map_python_to_config(self, python_content: Dict[str, Any]) -> Dict[str, Any]:
        """将Python配置映射到配置结构

        Args:
            python_content: Python配置内容

        Returns:
            Dict[str, Any]: 映射后的配置
        """
        # 简单映射，可以根据需要扩展
        return self._map_env_to_config(python_content)

    def _convert_env_value(self, key: str, value: str) -> Any:
        """转换环境变量值类型

        Args:
            key: 环境变量键
            value: 环境变量值

        Returns:
            Any: 转换后的值
        """
        # 布尔值转换
        if key in ["DEBUG", "AUTO_START"] or value.lower() in ["true", "false"]:
            return value.lower() in ["true", "1", "yes", "on"]

        # 整数转换
        if key in [
            "SERVER_PORT",
            "WORKERS",
            "MAX_TOKENS",
            "TIMEOUT",
            "MAX_FILE_SIZE",
            "SESSION_TIMEOUT",
        ]:
            try:
                return int(value)
            except ValueError:
                return value

        # 浮点数转换
        if key in ["TEMPERATURE"]:
            try:
                return float(value)
            except ValueError:
                return value

        return value

    def _set_nested_config(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """设置嵌套配置值

        Args:
            config: 配置字典
            path: 配置路径
            value: 配置值
        """
        keys = path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _save_migrated_config(self, config: Dict[str, Any]) -> bool:
        """保存迁移后的配置

        Args:
            config: 配置数据

        Returns:
            bool: 保存是否成功
        """
        try:
            # 保存到主配置文件
            main_config_path = self.config_center.paths.get_config_file("main")
            success = self.config_center._save_yaml_file(config, main_config_path)

            if success:
                self.logger.info(f"✅ 迁移配置已保存: {main_config_path}")

                # 重新加载配置中心
                self.config_center.reload_config()

            return success

        except Exception as e:
            self.logger.error(f"❌ 保存迁移配置失败: {e}")
            return False

    def _update_config_references(self) -> bool:
        """更新代码中的配置引用

        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info("开始更新配置引用")

            # 这里可以实现代码中配置引用的自动更新
            # 例如：将 os.getenv() 调用替换为 get_config() 调用

            # 目前只记录需要手动更新的文件
            files_to_update = [
                "project/src/main.py",
                "project/src/core/app.py",
                "project/src/utils/logger.py",
                "project/src/ai/parameter_parser.py",
            ]

            self.migration_report["manual_updates_needed"] = files_to_update

            self.logger.info(
                f"✅ 配置引用更新完成，需要手动更新 {len(files_to_update)} 个文件"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ 更新配置引用失败: {e}")
            return False

    def _generate_migration_summary(
        self, merged_config: Dict[str, Any], config_files: List[Dict[str, Any]]
    ) -> None:
        """生成迁移摘要

        Args:
            merged_config: 合并后的配置
            config_files: 配置文件列表
        """
        summary = {
            "total_files_scanned": len(config_files),
            "total_files_migrated": len(self.migration_report["migrated_configs"]),
            "total_config_keys": len(self._extract_config_keys(merged_config)),
            "config_sections": list(merged_config.keys()),
            "file_types": {},
            "errors_count": len(self.migration_report["errors"]),
            "warnings_count": len(self.migration_report["warnings"]),
        }

        # 统计文件类型
        for config_file in config_files:
            file_type = config_file["type"]
            summary["file_types"][file_type] = (
                summary["file_types"].get(file_type, 0) + 1
            )

        self.migration_report["summary"] = summary

    def _generate_report_content(self) -> str:
        """生成报告内容

        Returns:
            str: 报告内容
        """
        report = self.migration_report
        summary = report.get("summary", {})

        content = f"""# 配置迁移报告

## 迁移概览

- **开始时间**: {report.get('start_time', 'N/A')}
- **结束时间**: {report.get('end_time', 'N/A')}
- **迁移状态**: {report.get('status', 'N/A')}
- **扫描文件数**: {summary.get('total_files_scanned', 0)}
- **迁移文件数**: {summary.get('total_files_migrated', 0)}
- **配置项总数**: {summary.get('total_config_keys', 0)}
- **错误数量**: {summary.get('errors_count', 0)}
- **警告数量**: {summary.get('warnings_count', 0)}

## 配置结构

迁移后的配置包含以下主要部分：

"""

        # 添加配置部分
        for section in summary.get("config_sections", []):
            content += f"- {section}\n"

        content += "\n## 文件类型统计\n\n"

        # 添加文件类型统计
        for file_type, count in summary.get("file_types", {}).items():
            content += f"- {file_type}: {count} 个文件\n"

        content += "\n## 迁移的配置文件\n\n"

        # 添加迁移的文件列表
        for migrated in report.get("migrated_configs", []):
            content += f"- **{migrated['file']}** ({migrated['type']}) - {migrated['keys_count']} 个配置项\n"

        # 添加错误和警告
        if report.get("errors"):
            content += "\n## 错误\n\n"
            for error in report["errors"]:
                content += f"- ❌ {error}\n"

        if report.get("warnings"):
            content += "\n## 警告\n\n"
            for warning in report["warnings"]:
                content += f"- ⚠️ {warning}\n"

        # 添加手动更新建议
        if report.get("manual_updates_needed"):
            content += "\n## 需要手动更新的文件\n\n"
            content += "以下文件可能需要手动更新以使用新的配置管理中心：\n\n"
            for file_path in report["manual_updates_needed"]:
                content += f"- {file_path}\n"

        content += "\n## 使用新配置管理中心\n\n"
        content += """迁移完成后，可以使用以下方式访问配置：

```python
try:
    from core.config_center import get_config, set_config
except ImportError:
    def get_config(key, default=None):
        return default
    def set_config(key, value, save=True):
        return False

# 获取配置
app_name = get_config('app.name')
server_port = get_config('server.port', 8000)

# 设置配置
set_config('app.debug', True)
```

## 后续步骤

1. 验证迁移后的配置是否正确
2. 更新代码中的配置引用
3. 测试应用程序功能
4. 删除旧的配置文件（建议保留备份）
"""

        return content


def run_migration(project_root: Optional[Path] = None, dry_run: bool = False) -> bool:
    """运行配置迁移

    Args:
        project_root: 项目根目录
        dry_run: 是否为试运行

    Returns:
        bool: 迁移是否成功
    """
    migration = ConfigMigration(project_root)

    # 执行迁移
    success = migration.migrate_configs(dry_run)

    # 生成报告
    report_path = migration.generate_migration_report()

    print(f"\n配置迁移{'试运行' if dry_run else ''}完成！")
    print(f"迁移状态: {'成功' if success else '失败'}")
    print(f"详细报告: {report_path}")

    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="配置迁移工具")
    parser.add_argument("--project-root", type=Path, help="项目根目录")
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行（不实际修改文件）"
    )

    args = parser.parse_args()

    success = run_migration(args.project_root, args.dry_run)
    exit(0 if success else 1)
