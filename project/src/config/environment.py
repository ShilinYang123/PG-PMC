#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 环境管理器
"""

import os
import platform
import subprocess
import sys
import winreg
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from src.utils.logger import get_logger


@dataclass
class SystemInfo:
    """系统信息"""

    os_name: str
    os_version: str
    architecture: str
    python_version: str
    python_executable: str
    memory_total: int  # MB
    cpu_count: int


@dataclass
class CreoInfo:
    """Creo信息"""

    installed: bool
    version: str
    install_path: str
    executable_path: str
    config_path: str
    working_directory: str


@dataclass
class EnvironmentStatus:
    """环境状态"""

    system: SystemInfo
    creo: CreoInfo
    python_packages: Dict[str, str]
    environment_variables: Dict[str, str]
    path_directories: List[str]
    issues: List[str]
    recommendations: List[str]


class EnvironmentManager:
    """环境管理器

    负责检查和管理系统环境、Creo安装、Python依赖等
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

        # Creo可能的安装路径
        self.creo_search_paths = [
            r"C:\Program Files\PTC",
            r"C:\Program Files (x86)\PTC",
            r"D:\Program Files\PTC",
            r"D:\PTC",
        ]

        # 必需的Python包
        self.required_packages = {
            "openai": ">=1.0.0",
            "anthropic": ">=0.3.0",
            "pywin32": ">=306",
            "comtypes": ">=1.1.0",
            "numpy": ">=1.21.0",
            "pandas": ">=1.3.0",
            "pyyaml": ">=6.0",
            "click": ">=8.0.0",
            "loguru": ">=0.6.0",
            "rich": ">=12.0.0",
        }

    def check_environment(self) -> EnvironmentStatus:
        """检查完整环境状态

        Returns:
            EnvironmentStatus: 环境状态信息
        """
        try:
            self.logger.info("开始环境检查")

            # 检查系统信息
            system_info = self._get_system_info()

            # 检查Creo安装
            creo_info = self._get_creo_info()

            # 检查Python包
            python_packages = self._get_python_packages()

            # 检查环境变量
            env_vars = self._get_environment_variables()

            # 检查PATH
            path_dirs = self._get_path_directories()

            # 分析问题和建议
            issues, recommendations = self._analyze_environment(
                system_info, creo_info, python_packages
            )

            status = EnvironmentStatus(
                system=system_info,
                creo=creo_info,
                python_packages=python_packages,
                environment_variables=env_vars,
                path_directories=path_dirs,
                issues=issues,
                recommendations=recommendations,
            )

            self.logger.info("✅ 环境检查完成")
            return status

        except Exception as e:
            self.logger.error(f"环境检查失败: {e}")
            raise

    def _get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        try:
            # 获取内存信息
            import psutil

            memory_total = psutil.virtual_memory().total // (1024 * 1024)  # MB
        except ImportError:
            memory_total = 0

        return SystemInfo(
            os_name=platform.system(),
            os_version=platform.version(),
            architecture=platform.architecture()[0],
            python_version=platform.python_version(),
            python_executable=sys.executable,
            memory_total=memory_total,
            cpu_count=os.cpu_count() or 1,
        )

    def _get_creo_info(self) -> CreoInfo:
        """获取Creo安装信息"""
        try:
            # 从注册表查找Creo安装信息
            creo_info = self._find_creo_from_registry()

            if not creo_info["installed"]:
                # 从文件系统搜索
                creo_info = self._find_creo_from_filesystem()

            return CreoInfo(**creo_info)

        except Exception as e:
            self.logger.error(f"获取Creo信息失败: {e}")
            return CreoInfo(
                installed=False,
                version="未知",
                install_path="",
                executable_path="",
                config_path="",
                working_directory="",
            )

    def _find_creo_from_registry(self) -> Dict[str, Any]:
        """从Windows注册表查找Creo"""
        try:
            # 查找PTC注册表项
            ptc_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PTC")

            # 遍历子键查找Creo
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(ptc_key, i)
                    if "Creo" in subkey_name or "Pro" in subkey_name:
                        subkey = winreg.OpenKey(ptc_key, subkey_name)

                        try:
                            install_path = winreg.QueryValueEx(subkey, "InstallDir")[0]
                            version = subkey_name

                            # 查找可执行文件
                            exe_path = self._find_creo_executable(install_path)

                            if exe_path:
                                return {
                                    "installed": True,
                                    "version": version,
                                    "install_path": install_path,
                                    "executable_path": exe_path,
                                    "config_path": os.path.join(install_path, "text"),
                                    "working_directory": os.path.join(
                                        install_path, "work"
                                    ),
                                }
                        except FileNotFoundError:
                            pass
                        finally:
                            winreg.CloseKey(subkey)

                    i += 1
                except OSError:
                    break

            winreg.CloseKey(ptc_key)

        except Exception as e:
            self.logger.debug(f"注册表查找Creo失败: {e}")

        return {
            "installed": False,
            "version": "",
            "install_path": "",
            "executable_path": "",
            "config_path": "",
            "working_directory": "",
        }

    def _find_creo_from_filesystem(self) -> Dict[str, Any]:
        """从文件系统搜索Creo"""
        try:
            for search_path in self.creo_search_paths:
                if not os.path.exists(search_path):
                    continue

                # 搜索Creo目录
                for root, dirs, files in os.walk(search_path):
                    for dir_name in dirs:
                        if "Creo" in dir_name and any(
                            v in dir_name for v in ["7.0", "8.0", "9.0", "10.0"]
                        ):
                            creo_dir = os.path.join(root, dir_name)
                            exe_path = self._find_creo_executable(creo_dir)

                            if exe_path:
                                return {
                                    "installed": True,
                                    "version": dir_name,
                                    "install_path": creo_dir,
                                    "executable_path": exe_path,
                                    "config_path": os.path.join(creo_dir, "text"),
                                    "working_directory": os.path.join(creo_dir, "work"),
                                }

                    # 限制搜索深度
                    if root.count(os.sep) - search_path.count(os.sep) >= 2:
                        dirs.clear()

        except Exception as e:
            self.logger.debug(f"文件系统搜索Creo失败: {e}")

        return {
            "installed": False,
            "version": "",
            "install_path": "",
            "executable_path": "",
            "config_path": "",
            "working_directory": "",
        }

    def _find_creo_executable(self, install_path: str) -> str:
        """在安装目录中查找Creo可执行文件"""
        try:
            # 可能的可执行文件路径
            possible_paths = [
                os.path.join(
                    install_path, "Common Files", "x86e_win64", "bin", "parametric.exe"
                ),
                os.path.join(install_path, "Parametric", "bin", "parametric.exe"),
                os.path.join(install_path, "bin", "parametric.exe"),
                os.path.join(install_path, "parametric.exe"),
            ]

            for exe_path in possible_paths:
                if os.path.exists(exe_path):
                    return exe_path

            # 递归搜索
            for root, dirs, files in os.walk(install_path):
                if "parametric.exe" in files:
                    return os.path.join(root, "parametric.exe")

                # 限制搜索深度
                if root.count(os.sep) - install_path.count(os.sep) >= 3:
                    dirs.clear()

        except Exception as e:
            self.logger.debug(f"查找Creo可执行文件失败: {e}")

        return ""

    def _get_python_packages(self) -> Dict[str, str]:
        """获取已安装的Python包信息"""
        try:
            import pkg_resources

            installed_packages = {}

            for package_name in self.required_packages.keys():
                try:
                    package = pkg_resources.get_distribution(package_name)
                    installed_packages[package_name] = package.version
                except pkg_resources.DistributionNotFound:
                    installed_packages[package_name] = "未安装"

            return installed_packages

        except Exception as e:
            self.logger.error(f"获取Python包信息失败: {e}")
            return {}

    def _get_environment_variables(self) -> Dict[str, str]:
        """获取相关环境变量"""
        try:
            relevant_vars = [
                "PATH",
                "PYTHONPATH",
                "PRO_COMM_MSG_EXE",
                "PRO_DIRECTORY",
                "CREO_COMMON_FILES",
                "PTC_WF_ROOT",
                "PINGAO_WORK_DIR",
                "PINGAO_DATA_DIR",
                "PINGAO_TEMP_DIR",
            ]

            env_vars = {}
            for var in relevant_vars:
                env_vars[var] = os.environ.get(var, "未设置")

            return env_vars

        except Exception as e:
            self.logger.error(f"获取环境变量失败: {e}")
            return {}

    def _get_path_directories(self) -> List[str]:
        """获取PATH目录列表"""
        try:
            path_env = os.environ.get("PATH", "")
            return [p.strip() for p in path_env.split(os.pathsep) if p.strip()]

        except Exception as e:
            self.logger.error(f"获取PATH目录失败: {e}")
            return []

    def _analyze_environment(
        self,
        system_info: SystemInfo,
        creo_info: CreoInfo,
        python_packages: Dict[str, str],
    ) -> Tuple[List[str], List[str]]:
        """分析环境问题和建议"""
        issues = []
        recommendations = []

        try:
            # 检查操作系统
            if system_info.os_name != "Windows":
                issues.append("当前系统不是Windows，Creo仅支持Windows")
                recommendations.append("请在Windows系统上运行此程序")

            # 检查Python版本
            python_version = tuple(map(int, system_info.python_version.split(".")))
            if python_version < (3, 8):
                issues.append(f"Python版本过低: {system_info.python_version}")
                recommendations.append("请升级到Python 3.8或更高版本")

            # 检查内存
            if system_info.memory_total > 0 and system_info.memory_total < 8192:  # 8GB
                issues.append(f"系统内存较低: {system_info.memory_total}MB")
                recommendations.append("建议至少16GB内存以获得最佳性能")

            # 检查Creo安装
            if not creo_info.installed:
                issues.append("未检测到Creo安装")
                recommendations.append("请安装Creo Parametric 7.0或更高版本")
            elif not os.path.exists(creo_info.executable_path):
                issues.append("Creo可执行文件不存在")
                recommendations.append("请检查Creo安装路径配置")

            # 检查Python包
            missing_packages = []
            for package, required_version in self.required_packages.items():
                installed_version = python_packages.get(package, "未安装")
                if installed_version == "未安装":
                    missing_packages.append(package)

            if missing_packages:
                issues.append(f"缺少必需的Python包: {', '.join(missing_packages)}")
                recommendations.append(
                    f"请运行: pip install {' '.join(missing_packages)}"
                )

            # 检查架构兼容性
            if system_info.architecture != "64bit":
                issues.append("系统架构不是64位")
                recommendations.append("建议使用64位Windows系统")

        except Exception as e:
            self.logger.error(f"环境分析失败: {e}")
            issues.append("环境分析过程中出现错误")

        return issues, recommendations

    def install_missing_packages(self) -> bool:
        """安装缺失的Python包

        Returns:
            bool: 安装是否成功
        """
        try:
            self.logger.info("检查并安装缺失的Python包")

            python_packages = self._get_python_packages()
            missing_packages = []

            for package in self.required_packages.keys():
                if python_packages.get(package, "未安装") == "未安装":
                    missing_packages.append(package)

            if not missing_packages:
                self.logger.info("所有必需的包都已安装")
                return True

            self.logger.info(f"安装缺失的包: {missing_packages}")

            # 使用pip安装
            cmd = [sys.executable, "-m", "pip", "install"] + missing_packages

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                self.logger.info("✅ 包安装成功")
                return True
            else:
                self.logger.error(f"包安装失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"安装Python包失败: {e}")
            return False

    def setup_creo_environment(self, creo_path: str) -> bool:
        """设置Creo环境

        Args:
            creo_path: Creo安装路径

        Returns:
            bool: 设置是否成功
        """
        try:
            self.logger.info(f"设置Creo环境: {creo_path}")

            if not os.path.exists(creo_path):
                self.logger.error(f"Creo路径不存在: {creo_path}")
                return False

            # 查找bin目录
            bin_path = None
            for root, dirs, files in os.walk(creo_path):
                if "bin" in dirs and "parametric.exe" in os.listdir(
                    os.path.join(root, "bin")
                ):
                    bin_path = os.path.join(root, "bin")
                    break

            if not bin_path:
                self.logger.error("未找到Creo bin目录")
                return False

            # 添加到PATH
            current_path = os.environ.get("PATH", "")
            if bin_path not in current_path:
                os.environ["PATH"] = f"{bin_path};{current_path}"
                self.logger.info(f"已添加到PATH: {bin_path}")

            # 设置Creo环境变量
            os.environ["PRO_DIRECTORY"] = creo_path
            os.environ["CREO_COMMON_FILES"] = os.path.join(creo_path, "Common Files")

            self.logger.info("✅ Creo环境设置完成")
            return True

        except Exception as e:
            self.logger.error(f"设置Creo环境失败: {e}")
            return False

    def create_environment_report(self, output_file: str = None) -> str:
        """创建环境报告

        Args:
            output_file: 输出文件路径

        Returns:
            str: 报告内容
        """
        try:
            self.logger.info("生成环境报告")

            status = self.check_environment()

            report_lines = [
                "# PinGao AI设计助理 - 环境报告",
                f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 系统信息",
                f"操作系统: {status.system.os_name} {status.system.os_version}",
                f"架构: {status.system.architecture}",
                f"Python版本: {status.system.python_version}",
                f"Python路径: {status.system.python_executable}",
                f"内存: {status.system.memory_total}MB",
                f"CPU核心数: {status.system.cpu_count}",
                "",
                "## Creo信息",
                f"已安装: {'是' if status.creo.installed else '否'}",
                f"版本: {status.creo.version}",
                f"安装路径: {status.creo.install_path}",
                f"可执行文件: {status.creo.executable_path}",
                "",
                "## Python包",
            ]

            for package, version in status.python_packages.items():
                report_lines.append(f"{package}: {version}")

            if status.issues:
                report_lines.extend(
                    [
                        "",
                        "## 发现的问题",
                    ]
                )
                for issue in status.issues:
                    report_lines.append(f"- {issue}")

            if status.recommendations:
                report_lines.extend(
                    [
                        "",
                        "## 建议",
                    ]
                )
                for rec in status.recommendations:
                    report_lines.append(f"- {rec}")

            report_content = "\n".join(report_lines)

            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report_content)
                self.logger.info(f"环境报告已保存: {output_file}")

            return report_content

        except Exception as e:
            self.logger.error(f"生成环境报告失败: {e}")
            return "环境报告生成失败"
