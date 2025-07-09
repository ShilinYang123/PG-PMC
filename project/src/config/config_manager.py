#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置管理器
"""

import json
# import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.utils.encryption import decrypt_data, encrypt_data
from src.utils.logger import get_logger

from .settings import Settings


class ConfigManager:
    """配置管理器

    负责配置文件的加载、保存、验证和管理
    """

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.logger = get_logger(self.__class__.__name__)

        # 默认配置文件路径
        self.config_file = config_file or "config/settings.yaml"
        self.config_dir = Path(self.config_file).parent

        # 备份配置文件路径
        self.backup_file = self.config_dir / "settings_backup.yaml"

        # 用户配置文件路径
        self.user_config_file = self.config_dir / "user_settings.yaml"

        # 当前设置
        self._settings: Optional[Settings] = None

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> Settings:
        """加载配置设置

        Returns:
            Settings: 配置设置对象
        """
        try:
            self.logger.info("加载配置设置")

            # 尝试加载用户配置
            if self.user_config_file.exists():
                self.logger.info(f"加载用户配置: {self.user_config_file}")
                settings = self._load_from_file(self.user_config_file)
            # 尝试加载默认配置
            elif Path(self.config_file).exists():
                self.logger.info(f"加载默认配置: {self.config_file}")
                settings = self._load_from_file(self.config_file)
            else:
                self.logger.info("使用默认配置")
                settings = Settings()
                # 保存默认配置
                self.save_settings(settings)

            # 验证配置
            errors = settings.validate()
            if errors:
                self.logger.warning(f"配置验证发现问题: {errors}")
                for error in errors:
                    self.logger.warning(f"  - {error}")

            # 解密敏感信息
            self._decrypt_sensitive_data(settings)

            self._settings = settings
            self.logger.info("✅ 配置加载完成")

            return settings

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            # 返回默认配置
            self._settings = Settings()
            return self._settings

    def save_settings(self, settings: Settings, user_config: bool = True) -> bool:
        """保存配置设置

        Args:
            settings: 配置设置对象
            user_config: 是否保存为用户配置

        Returns:
            bool: 保存是否成功
        """
        try:
            self.logger.info("保存配置设置")

            # 创建备份
            if user_config and self.user_config_file.exists():
                self._create_backup()

            # 加密敏感信息
            settings_copy = self._encrypt_sensitive_data(settings)

            # 选择保存文件
            target_file = self.user_config_file if user_config else self.config_file

            # 保存配置
            success = self._save_to_file(settings_copy, target_file)

            if success:
                self._settings = settings
                self.logger.info(f"✅ 配置已保存: {target_file}")

            return success

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False

    def get_settings(self) -> Settings:
        """获取当前配置设置

        Returns:
            Settings: 配置设置对象
        """
        if self._settings is None:
            return self.load_settings()
        return self._settings

    def update_setting(self, key_path: str, value: Any) -> bool:
        """更新单个配置项

        Args:
            key_path: 配置项路径，如 'creo.connection_timeout'
            value: 新值

        Returns:
            bool: 更新是否成功
        """
        try:
            settings = self.get_settings()

            # 解析键路径
            keys = key_path.split(".")
            obj = settings

            # 导航到目标对象
            for key in keys[:-1]:
                if hasattr(obj, key):
                    obj = getattr(obj, key)
                else:
                    self.logger.error(f"配置路径不存在: {key_path}")
                    return False

            # 设置值
            final_key = keys[-1]
            if hasattr(obj, final_key):
                setattr(obj, final_key, value)
                self.logger.info(f"配置已更新: {key_path} = {value}")
                return self.save_settings(settings)
            else:
                self.logger.error(f"配置项不存在: {final_key}")
                return False

        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """获取单个配置项

        Args:
            key_path: 配置项路径，如 'creo.connection_timeout'
            default: 默认值

        Returns:
            Any: 配置值
        """
        try:
            settings = self.get_settings()

            # 解析键路径
            keys = key_path.split(".")
            obj = settings

            # 导航到目标值
            for key in keys:
                if hasattr(obj, key):
                    obj = getattr(obj, key)
                else:
                    return default

            return obj

        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return default

    def reset_to_defaults(self) -> bool:
        """重置为默认配置

        Returns:
            bool: 重置是否成功
        """
        try:
            self.logger.info("重置为默认配置")

            # 创建备份
            if self.user_config_file.exists():
                self._create_backup()

            # 创建默认设置
            default_settings = Settings()

            # 保存默认设置
            success = self.save_settings(default_settings)

            if success:
                self.logger.info("✅ 配置已重置为默认值")

            return success

        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False

    def export_config(self, export_file: str, format: str = "yaml") -> bool:
        """导出配置

        Args:
            export_file: 导出文件路径
            format: 导出格式 (yaml, json)

        Returns:
            bool: 导出是否成功
        """
        try:
            self.logger.info(f"导出配置到: {export_file}")

            settings = self.get_settings()
            settings_dict = asdict(settings)

            export_path = Path(export_file)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "json":
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(settings_dict, f, indent=2, ensure_ascii=False)
            else:  # yaml
                with open(export_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        settings_dict,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

            self.logger.info(f"✅ 配置已导出: {export_file}")
            return True

        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False

    def import_config(self, import_file: str) -> bool:
        """导入配置

        Args:
            import_file: 导入文件路径

        Returns:
            bool: 导入是否成功
        """
        try:
            self.logger.info(f"导入配置从: {import_file}")

            import_path = Path(import_file)
            if not import_path.exists():
                self.logger.error(f"导入文件不存在: {import_file}")
                return False

            # 创建备份
            self._create_backup()

            # 加载导入的配置
            imported_settings = self._load_from_file(import_path)

            # 验证配置
            errors = imported_settings.validate()
            if errors:
                self.logger.warning(f"导入的配置存在问题: {errors}")
                # 可以选择是否继续导入

            # 保存导入的配置
            success = self.save_settings(imported_settings)

            if success:
                self.logger.info(f"✅ 配置已导入: {import_file}")

            return success

        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False

    def _load_from_file(self, file_path: Path) -> Settings:
        """从文件加载配置"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    data = json.load(f)
                else:  # yaml
                    data = yaml.safe_load(f)

            return Settings.from_dict(data)

        except Exception as e:
            self.logger.error(f"从文件加载配置失败: {e}")
            raise

    def _save_to_file(self, settings: Settings, file_path: Path) -> bool:
        """保存配置到文件"""
        try:
            settings_dict = asdict(settings)

            with open(file_path, "w", encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    json.dump(settings_dict, f, indent=2, ensure_ascii=False)
                else:  # yaml
                    yaml.dump(
                        settings_dict,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

            return True

        except Exception as e:
            self.logger.error(f"保存配置到文件失败: {e}")
            return False

    def _create_backup(self) -> bool:
        """创建配置备份"""
        try:
            if self.user_config_file.exists():
                import shutil

                shutil.copy2(self.user_config_file, self.backup_file)
                self.logger.info(f"配置备份已创建: {self.backup_file}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"创建配置备份失败: {e}")
            return False

    def restore_backup(self) -> bool:
        """恢复配置备份

        Returns:
            bool: 恢复是否成功
        """
        try:
            if not self.backup_file.exists():
                self.logger.error("备份文件不存在")
                return False

            import shutil

            shutil.copy2(self.backup_file, self.user_config_file)

            # 重新加载配置
            self._settings = None
            self.load_settings()

            self.logger.info("✅ 配置已从备份恢复")
            return True

        except Exception as e:
            self.logger.error(f"恢复配置备份失败: {e}")
            return False

    def _encrypt_sensitive_data(self, settings: Settings) -> Settings:
        """加密敏感数据"""
        try:
            if not settings.security.encrypt_api_keys:
                return settings

            # 创建设置副本
            import copy

            settings_copy = copy.deepcopy(settings)

            # 加密API密钥
            if settings_copy.ai.openai_api_key:
                settings_copy.ai.openai_api_key = encrypt_data(
                    settings_copy.ai.openai_api_key, settings.security.encryption_key
                )

            if settings_copy.ai.claude_api_key:
                settings_copy.ai.claude_api_key = encrypt_data(
                    settings_copy.ai.claude_api_key, settings.security.encryption_key
                )

            return settings_copy

        except Exception as e:
            self.logger.error(f"加密敏感数据失败: {e}")
            return settings

    def _decrypt_sensitive_data(self, settings: Settings):
        """解密敏感数据"""
        try:
            if not settings.security.encrypt_api_keys:
                return

            # 解密API密钥
            if settings.ai.openai_api_key:
                try:
                    settings.ai.openai_api_key = decrypt_data(
                        settings.ai.openai_api_key, settings.security.encryption_key
                    )
                except Exception:
                    self.logger.warning("OpenAI API密钥解密失败")

            if settings.ai.claude_api_key:
                try:
                    settings.ai.claude_api_key = decrypt_data(
                        settings.ai.claude_api_key, settings.security.encryption_key
                    )
                except Exception:
                    self.logger.warning("Claude API密钥解密失败")

        except Exception as e:
            self.logger.error(f"解密敏感数据失败: {e}")

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息

        Returns:
            Dict: 配置信息
        """
        try:
            settings = self.get_settings()

            info = {
                "config_file": str(self.config_file),
                "user_config_file": str(self.user_config_file),
                "backup_file": str(self.backup_file),
                "config_exists": Path(self.config_file).exists(),
                "user_config_exists": self.user_config_file.exists(),
                "backup_exists": self.backup_file.exists(),
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "debug_mode": settings.debug_mode,
                "creo_available": settings.is_creo_available(),
                "validation_errors": settings.validate(),
            }

            return info

        except Exception as e:
            self.logger.error(f"获取配置信息失败: {e}")
            return {}

    def cleanup_old_configs(self, keep_days: int = 30) -> int:
        """清理旧的配置文件

        Args:
            keep_days: 保留天数

        Returns:
            int: 清理的文件数量
        """
        try:
            import time
            # from datetime import datetime

            cutoff_time = time.time() - (keep_days * 24 * 3600)
            cleaned_count = 0

            # 查找配置目录中的旧文件
            for file_path in self.config_dir.glob("*_backup_*.yaml"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    self.logger.info(f"已清理旧配置文件: {file_path}")

            if cleaned_count > 0:
                self.logger.info(f"✅ 已清理 {cleaned_count} 个旧配置文件")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"清理旧配置文件失败: {e}")
            return 0
