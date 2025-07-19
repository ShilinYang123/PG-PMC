#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 文件工具
"""

import csv
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.utils.logger import get_logger


class FileUtils:
    """文件工具类

    提供文件和目录操作的实用工具方法
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def ensure_directory(self, path: Union[str, Path]) -> bool:
        """确保目录存在

        Args:
            path: 目录路径

        Returns:
            bool: 是否成功
        """
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"确保目录存在: {path}")
            return True

        except Exception as e:
            self.logger.error(f"创建目录失败 {path}: {e}")
            return False

    def copy_file(
        self, src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False
    ) -> bool:
        """复制文件

        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)

            if not src_path.exists():
                self.logger.error(f"源文件不存在: {src_path}")
                return False

            if dst_path.exists() and not overwrite:
                self.logger.warning(f"目标文件已存在且不允许覆盖: {dst_path}")
                return False

            # 确保目标目录存在
            self.ensure_directory(dst_path.parent)

            shutil.copy2(src_path, dst_path)
            self.logger.info(f"文件复制成功: {src_path} -> {dst_path}")
            return True

        except Exception as e:
            self.logger.error(f"复制文件失败: {e}")
            return False

    def move_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """移动文件

        Args:
            src: 源文件路径
            dst: 目标文件路径

        Returns:
            bool: 是否成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)

            if not src_path.exists():
                self.logger.error(f"源文件不存在: {src_path}")
                return False

            # 确保目标目录存在
            self.ensure_directory(dst_path.parent)

            shutil.move(str(src_path), str(dst_path))
            self.logger.info(f"文件移动成功: {src_path} -> {dst_path}")
            return True

        except Exception as e:
            self.logger.error(f"移动文件失败: {e}")
            return False

    def delete_file(self, path: Union[str, Path]) -> bool:
        """删除文件

        Args:
            path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            file_path = Path(path)

            if not file_path.exists():
                self.logger.warning(f"文件不存在: {file_path}")
                return True

            if file_path.is_file():
                file_path.unlink()
                self.logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                self.logger.error(f"路径不是文件: {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            return False

    def delete_directory(self, path: Union[str, Path], force: bool = False) -> bool:
        """删除目录

        Args:
            path: 目录路径
            force: 是否强制删除非空目录

        Returns:
            bool: 是否成功
        """
        try:
            dir_path = Path(path)

            if not dir_path.exists():
                self.logger.warning(f"目录不存在: {dir_path}")
                return True

            if not dir_path.is_dir():
                self.logger.error(f"路径不是目录: {dir_path}")
                return False

            if force:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()  # 只能删除空目录

            self.logger.info(f"目录删除成功: {dir_path}")
            return True

        except Exception as e:
            self.logger.error(f"删除目录失败: {e}")
            return False

    def get_file_size(self, path: Union[str, Path]) -> Optional[int]:
        """获取文件大小

        Args:
            path: 文件路径

        Returns:
            Optional[int]: 文件大小（字节），如果失败返回None
        """
        try:
            file_path = Path(path)

            if not file_path.exists() or not file_path.is_file():
                return None

            return file_path.stat().st_size

        except Exception as e:
            self.logger.error(f"获取文件大小失败: {e}")
            return None

    def get_file_hash(
        self, path: Union[str, Path], algorithm: str = "md5"
    ) -> Optional[str]:
        """计算文件哈希值

        Args:
            path: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256等）

        Returns:
            Optional[str]: 哈希值，如果失败返回None
        """
        try:
            file_path = Path(path)

            if not file_path.exists() or not file_path.is_file():
                return None

            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {e}")
            return None

    def list_files(
        self, directory: Union[str, Path], pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件名模式
            recursive: 是否递归搜索

        Returns:
            List[Path]: 文件路径列表
        """
        try:
            dir_path = Path(directory)

            if not dir_path.exists() or not dir_path.is_dir():
                return []

            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))

            # 只返回文件，不包括目录
            return [f for f in files if f.is_file()]

        except Exception as e:
            self.logger.error(f"列出文件失败: {e}")
            return []

    def read_text_file(
        self, path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """读取文本文件

        Args:
            path: 文件路径
            encoding: 文件编码

        Returns:
            Optional[str]: 文件内容，如果失败返回None
        """
        try:
            file_path = Path(path)

            if not file_path.exists() or not file_path.is_file():
                return None

            with open(file_path, "r", encoding=encoding) as f:
                return f.read()

        except Exception as e:
            self.logger.error(f"读取文本文件失败: {e}")
            return None

    def write_text_file(
        self,
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
        append: bool = False,
    ) -> bool:
        """写入文本文件

        Args:
            path: 文件路径
            content: 文件内容
            encoding: 文件编码
            append: 是否追加模式

        Returns:
            bool: 是否成功
        """
        try:
            file_path = Path(path)

            # 确保目录存在
            self.ensure_directory(file_path.parent)

            mode = "a" if append else "w"

            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)

            self.logger.debug(f"写入文本文件成功: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"写入文本文件失败: {e}")
            return False

    def read_json_file(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """读取JSON文件

        Args:
            path: 文件路径

        Returns:
            Optional[Dict[str, Any]]: JSON数据，如果失败返回None
        """
        try:
            content = self.read_text_file(path)
            if content is None:
                return None

            return json.loads(content)

        except Exception as e:
            self.logger.error(f"读取JSON文件失败: {e}")
            return None

    def write_json_file(
        self, path: Union[str, Path], data: Dict[str, Any], indent: int = 2
    ) -> bool:
        """写入JSON文件

        Args:
            path: 文件路径
            data: JSON数据
            indent: 缩进空格数

        Returns:
            bool: 是否成功
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.write_text_file(path, content)

        except Exception as e:
            self.logger.error(f"写入JSON文件失败: {e}")
            return False

    def read_yaml_file(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """读取YAML文件

        Args:
            path: 文件路径

        Returns:
            Optional[Dict[str, Any]]: YAML数据，如果失败返回None
        """
        try:
            content = self.read_text_file(path)
            if content is None:
                return None

            return yaml.safe_load(content)

        except Exception as e:
            self.logger.error(f"读取YAML文件失败: {e}")
            return None

    def write_yaml_file(self, path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """写入YAML文件

        Args:
            path: 文件路径
            data: YAML数据

        Returns:
            bool: 是否成功
        """
        try:
            content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            return self.write_text_file(path, content)

        except Exception as e:
            self.logger.error(f"写入YAML文件失败: {e}")
            return False

    def read_csv_file(
        self, path: Union[str, Path], delimiter: str = ","
    ) -> Optional[List[Dict[str, str]]]:
        """读取CSV文件

        Args:
            path: 文件路径
            delimiter: 分隔符

        Returns:
            Optional[List[Dict[str, str]]]: CSV数据，如果失败返回None
        """
        try:
            file_path = Path(path)

            if not file_path.exists() or not file_path.is_file():
                return None

            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)

        except Exception as e:
            self.logger.error(f"读取CSV文件失败: {e}")
            return None

    def write_csv_file(
        self, path: Union[str, Path], data: List[Dict[str, str]], delimiter: str = ","
    ) -> bool:
        """写入CSV文件

        Args:
            path: 文件路径
            data: CSV数据
            delimiter: 分隔符

        Returns:
            bool: 是否成功
        """
        try:
            if not data:
                return False

            file_path = Path(path)

            # 确保目录存在
            self.ensure_directory(file_path.parent)

            fieldnames = data[0].keys()

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)

            self.logger.debug(f"写入CSV文件成功: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"写入CSV文件失败: {e}")
            return False

    def create_backup(
        self,
        source: Union[str, Path],
        backup_dir: Union[str, Path],
        timestamp: bool = True,
    ) -> Optional[Path]:
        """创建备份

        Args:
            source: 源文件或目录路径
            backup_dir: 备份目录
            timestamp: 是否在备份名称中添加时间戳

        Returns:
            Optional[Path]: 备份文件路径，如果失败返回None
        """
        try:
            source_path = Path(source)
            backup_dir_path = Path(backup_dir)

            if not source_path.exists():
                self.logger.error(f"源路径不存在: {source_path}")
                return None

            # 确保备份目录存在
            self.ensure_directory(backup_dir_path)

            # 生成备份文件名
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source_path.name}_{timestamp_str}"
            else:
                backup_name = source_path.name

            backup_path = backup_dir_path / backup_name

            # 执行备份
            if source_path.is_file():
                shutil.copy2(source_path, backup_path)
            else:
                shutil.copytree(source_path, backup_path)

            self.logger.info(f"备份创建成功: {source_path} -> {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return None

    def create_zip_archive(
        self, source: Union[str, Path], archive_path: Union[str, Path]
    ) -> bool:
        """创建ZIP压缩包

        Args:
            source: 源文件或目录路径
            archive_path: 压缩包路径

        Returns:
            bool: 是否成功
        """
        try:
            source_path = Path(source)
            archive_file = Path(archive_path)

            if not source_path.exists():
                self.logger.error(f"源路径不存在: {source_path}")
                return False

            # 确保目标目录存在
            self.ensure_directory(archive_file.parent)

            with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                if source_path.is_file():
                    zipf.write(source_path, source_path.name)
                else:
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path.parent)
                            zipf.write(file_path, arcname)

            self.logger.info(f"ZIP压缩包创建成功: {archive_file}")
            return True

        except Exception as e:
            self.logger.error(f"创建ZIP压缩包失败: {e}")
            return False

    def extract_zip_archive(
        self, archive_path: Union[str, Path], extract_dir: Union[str, Path]
    ) -> bool:
        """解压ZIP压缩包

        Args:
            archive_path: 压缩包路径
            extract_dir: 解压目录

        Returns:
            bool: 是否成功
        """
        try:
            archive_file = Path(archive_path)
            extract_path = Path(extract_dir)

            if not archive_file.exists() or not archive_file.is_file():
                self.logger.error(f"压缩包不存在: {archive_file}")
                return False

            # 确保解压目录存在
            self.ensure_directory(extract_path)

            with zipfile.ZipFile(archive_file, "r") as zipf:
                zipf.extractall(extract_path)

            self.logger.info(f"ZIP压缩包解压成功: {archive_file} -> {extract_path}")
            return True

        except Exception as e:
            self.logger.error(f"解压ZIP压缩包失败: {e}")
            return False

    @contextmanager
    def temporary_directory(self):
        """临时目录上下文管理器

        Yields:
            Path: 临时目录路径
        """
        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp())
            self.logger.debug(f"创建临时目录: {temp_dir}")
            yield temp_dir
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
                self.logger.debug(f"清理临时目录: {temp_dir}")

    @contextmanager
    def temporary_file(self, suffix: str = "", prefix: str = "tmp"):
        """临时文件上下文管理器

        Args:
            suffix: 文件后缀
            prefix: 文件前缀

        Yields:
            Path: 临时文件路径
        """
        temp_file = None
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # 关闭文件描述符
            temp_file = Path(temp_path)
            self.logger.debug(f"创建临时文件: {temp_file}")
            yield temp_file
        finally:
            if temp_file and temp_file.exists():
                temp_file.unlink()
                self.logger.debug(f"清理临时文件: {temp_file}")

    def get_directory_size(self, directory: Union[str, Path]) -> int:
        """获取目录大小

        Args:
            directory: 目录路径

        Returns:
            int: 目录大小（字节）
        """
        try:
            dir_path = Path(directory)

            if not dir_path.exists() or not dir_path.is_dir():
                return 0

            total_size = 0
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            return total_size

        except Exception as e:
            self.logger.error(f"获取目录大小失败: {e}")
            return 0

    def clean_directory(
        self, directory: Union[str, Path], keep_patterns: List[str] = None
    ) -> bool:
        """清理目录

        Args:
            directory: 目录路径
            keep_patterns: 保留文件的模式列表

        Returns:
            bool: 是否成功
        """
        try:
            dir_path = Path(directory)

            if not dir_path.exists() or not dir_path.is_dir():
                return False

            keep_patterns = keep_patterns or []

            for item in dir_path.iterdir():
                # 检查是否需要保留
                should_keep = False
                for pattern in keep_patterns:
                    if item.match(pattern):
                        should_keep = True
                        break

                if not should_keep:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

            self.logger.info(f"目录清理完成: {dir_path}")
            return True

        except Exception as e:
            self.logger.error(f"清理目录失败: {e}")
            return False

    def find_files_by_content(
        self, directory: Union[str, Path], search_text: str, file_pattern: str = "*.py"
    ) -> List[Path]:
        """根据内容查找文件

        Args:
            directory: 搜索目录
            search_text: 搜索文本
            file_pattern: 文件模式

        Returns:
            List[Path]: 包含搜索文本的文件列表
        """
        try:
            dir_path = Path(directory)

            if not dir_path.exists() or not dir_path.is_dir():
                return []

            matching_files = []

            for file_path in dir_path.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        content = self.read_text_file(file_path)
                        if content and search_text in content:
                            matching_files.append(file_path)
                    except Exception:
                        # 忽略无法读取的文件
                        continue

            return matching_files

        except Exception as e:
            self.logger.error(f"根据内容查找文件失败: {e}")
            return []


# 全局文件工具实例
file_utils = FileUtils()
