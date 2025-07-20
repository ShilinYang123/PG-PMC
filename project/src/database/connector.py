#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - Creo连接器
"""

import os
import time
from pathlib import Path
from typing import Any, Optional

try:
    import pythoncom
    import win32com.client
except ImportError:
    win32com = None
    pythoncom = None

from src.utils.logger import get_logger


class CreoConnectionError(Exception):
    """Creo连接异常"""

    pass


class CreoConnector:
    """Creo软件连接器

    负责与Creo Parametric软件建立COM连接，提供基础的连接管理功能
    """

    def __init__(self, creo_path: str = None, timeout: int = 30):
        """初始化Creo连接器

        Args:
            creo_path: Creo安装路径
            timeout: 连接超时时间（秒）
        """
        self.creo_path = creo_path
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)

        # COM对象
        self._creo_app: Optional[Any] = None
        self._session: Optional[Any] = None
        self._connected = False

        # 检查Windows COM支持
        if win32com is None:
            raise ImportError("缺少pywin32依赖，请运行: pip install pywin32")

    def connect(self) -> bool:
        """连接到Creo软件

        Returns:
            bool: 连接是否成功
        """
        try:
            self.logger.info("正在连接Creo Parametric...")

            # 初始化COM
            pythoncom.CoInitialize()

            # 尝试连接现有的Creo实例
            try:
                self._creo_app = win32com.client.GetActiveObject(
                    "CreoParametric.Application"
                )
                self.logger.info("已连接到现有的Creo实例")
            except Exception:
                # 启动新的Creo实例
                self.logger.info("启动新的Creo实例...")
                if not self._start_creo():
                    return False

                # 连接到新启动的实例
                max_attempts = self.timeout
                for attempt in range(max_attempts):
                    try:
                        self._creo_app = win32com.client.GetActiveObject(
                            "CreoParametric.Application"
                        )
                        break
                    except Exception:
                        if attempt < max_attempts - 1:
                            time.sleep(1)
                        else:
                            raise CreoConnectionError("无法连接到Creo实例")

            # 获取会话
            self._session = self._creo_app.CurrentSession
            if not self._session:
                raise CreoConnectionError("无法获取Creo会话")

            self._connected = True
            self.logger.info("✅ Creo连接成功")

            # 获取Creo版本信息
            try:
                version = self._creo_app.Version
                self.logger.info(f"Creo版本: {version}")
            except Exception:
                self.logger.warning("无法获取Creo版本信息")

            return True

        except Exception as e:
            self.logger.error(f"Creo连接失败: {e}")
            self._connected = False
            return False

    def _start_creo(self) -> bool:
        """启动Creo软件

        Returns:
            bool: 启动是否成功
        """
        try:
            if self.creo_path and Path(self.creo_path).exists():
                creo_exe = Path(self.creo_path) / "bin" / "parametric.exe"
            else:
                # 尝试从常见安装路径查找
                common_paths = [
                    r"C:\Program Files\PTC\Creo 9.0.0.0\Parametric\bin\parametric.exe",
                    r"C:\Program Files\PTC\Creo 8.0.0.0\Parametric\bin\parametric.exe",
                    r"C:\Program Files\PTC\Creo 7.0.0.0\Parametric\bin\parametric.exe",
                ]

                creo_exe = None
                for path in common_paths:
                    if Path(path).exists():
                        creo_exe = Path(path)
                        break

                if not creo_exe:
                    raise CreoConnectionError(
                        "未找到Creo安装路径，请在配置中指定creo_path"
                    )

            self.logger.info(f"启动Creo: {creo_exe}")
            os.startfile(str(creo_exe))

            # 等待Creo启动
            self.logger.info("等待Creo启动...")
            time.sleep(10)  # 给Creo足够的启动时间

            return True

        except Exception as e:
            self.logger.error(f"启动Creo失败: {e}")
            return False

    def disconnect(self):
        """断开Creo连接"""
        try:
            if self._connected:
                self.logger.info("正在断开Creo连接...")

                # 清理COM对象
                self._session = None
                self._creo_app = None

                # 清理COM
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

                self._connected = False
                self.logger.info("Creo连接已断开")

        except Exception as e:
            self.logger.error(f"断开Creo连接时出错: {e}")

    def test_connection(self) -> bool:
        """测试Creo连接

        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not self._connected:
                if not self.connect():
                    return False

            # 测试基本操作
            if self._session:
                # 尝试获取当前模型
                try:
                    self._session.CurrentModel
                    self.logger.info("连接测试成功 - 可以访问Creo会话")
                    return True
                except Exception:
                    self.logger.info("连接测试成功 - Creo会话可用（无当前模型）")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._session is not None

    @property
    def session(self):
        """获取Creo会话对象"""
        if not self.is_connected:
            raise CreoConnectionError("未连接到Creo")
        return self._session

    @property
    def application(self):
        """获取Creo应用程序对象"""
        if not self.is_connected:
            raise CreoConnectionError("未连接到Creo")
        return self._creo_app

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()