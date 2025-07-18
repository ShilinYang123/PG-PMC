#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - CREOSON连接器
支持Creo 10的现代化自动化接口
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from src.core.unified_logging import get_logger


class CreosonConnectionError(Exception):
    """CREOSON连接异常"""

    pass


class CreosonConnector:
    """CREOSON连接器

    提供基于JSON API的Creo Parametric自动化接口
    支持Creo 10的现代化自动化功能
    """

    def __init__(
        self,
        server_url: str = "http://localhost:9056",
        creo_path: str = None,
        timeout: int = 30,
    ):
        """初始化CREOSON连接器

        Args:
            server_url: CREOSON服务器地址
            creo_path: Creo安装路径
            timeout: 连接超时时间（秒）
        """
        self.server_url = server_url
        self.creo_path = creo_path
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)

        # 连接状态
        self._connected = False
        self._session_id = None

    def connect(self) -> bool:
        """连接到CREOSON服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            self.logger.info("正在连接CREOSON服务器...")

            # 检查CREOSON服务器是否运行
            if not self._check_creoson_server():
                self.logger.info("CREOSON服务器未运行，尝试启动...")
                if not self._start_creoson_server():
                    raise CreosonConnectionError("启动CREOSON服务器失败")

            # 连接到Creo
            response = self._send_request({"command": "creo", "function": "connect"})

            if response and response.get("status") == "success":
                self._connected = True
                self._session_id = response.get("sessionId")
                self.logger.info("✅ CREOSON连接成功")
                return True
            else:
                raise CreosonConnectionError(f"连接失败: {response}")

        except Exception as e:
            self.logger.error(f"CREOSON连接失败: {e}")
            return False

    def disconnect(self):
        """断开CREOSON连接"""
        try:
            if self._connected:
                self._send_request({"command": "creo", "function": "disconnect"})
                self._connected = False
                self._session_id = None
                self.logger.info("CREOSON连接已断开")
        except Exception as e:
            self.logger.error(f"断开CREOSON连接失败: {e}")

    def _check_creoson_server(self) -> bool:
        """检查CREOSON服务器是否运行"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _start_creoson_server(self) -> bool:
        """启动CREOSON服务器"""
        try:
            # 这里需要根据实际CREOSON安装路径调整
            creoson_path = "C:\\CREOSON\\CreosonServer.exe"  # 默认路径

            if not Path(creoson_path).exists():
                self.logger.warning(f"CREOSON服务器未找到: {creoson_path}")
                return False

            # 启动CREOSON服务器
            subprocess.Popen(
                [creoson_path], creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            # 等待服务器启动
            for _ in range(30):
                if self._check_creoson_server():
                    self.logger.info("CREOSON服务器启动成功")
                    return True
                time.sleep(1)

            return False

        except Exception as e:
            self.logger.error(f"启动CREOSON服务器失败: {e}")
            return False

    def _send_request(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送JSON请求到CREOSON服务器

        Args:
            data: 请求数据

        Returns:
            响应数据
        """
        try:
            if self._session_id:
                data["sessionId"] = self._session_id

            response = requests.post(
                f"{self.server_url}/creoson", json=data, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"请求失败: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"发送请求失败: {e}")
            return None

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def create_part(self, name: str, template: str = "mmns_part_solid") -> bool:
        """创建新零件

        Args:
            name: 零件名称
            template: 模板名称

        Returns:
            bool: 创建是否成功
        """
        try:
            response = self._send_request(
                {
                    "command": "file",
                    "function": "new",
                    "data": {"name": name, "type": "part", "template": template},
                }
            )

            return response and response.get("status") == "success"

        except Exception as e:
            self.logger.error(f"创建零件失败: {e}")
            return False

    def create_cylinder_feature(self, diameter: float, height: float) -> bool:
        """创建圆柱体特征

        Args:
            diameter: 直径（毫米）
            height: 高度（毫米）

        Returns:
            bool: 创建是否成功
        """
        try:
            # 创建草图
            sketch_response = self._send_request(
                {
                    "command": "sketch",
                    "function": "create",
                    "data": {"name": "cylinder_sketch", "plane": "FRONT"},
                }
            )

            if not (sketch_response and sketch_response.get("status") == "success"):
                return False

            # 绘制圆形
            circle_response = self._send_request(
                {
                    "command": "sketch",
                    "function": "create_circle",
                    "data": {"center": [0, 0], "radius": diameter / 2},
                }
            )

            if not (circle_response and circle_response.get("status") == "success"):
                return False

            # 退出草图
            self._send_request({"command": "sketch", "function": "exit"})

            # 拉伸特征
            extrude_response = self._send_request(
                {
                    "command": "feature",
                    "function": "create_extrude",
                    "data": {"name": "cylinder_extrude", "depth": height},
                }
            )

            return extrude_response and extrude_response.get("status") == "success"

        except Exception as e:
            self.logger.error(f"创建圆柱体特征失败: {e}")
            return False

    def set_material(self, material_name: str) -> bool:
        """设置材料

        Args:
            material_name: 材料名称

        Returns:
            bool: 设置是否成功
        """
        try:
            response = self._send_request(
                {
                    "command": "part",
                    "function": "set_material",
                    "data": {"material": material_name},
                }
            )

            return response and response.get("status") == "success"

        except Exception as e:
            self.logger.error(f"设置材料失败: {e}")
            return False

    def save_model(self, filename: str = None) -> bool:
        """保存模型

        Args:
            filename: 文件名（可选）

        Returns:
            bool: 保存是否成功
        """
        try:
            data = {"command": "file", "function": "save"}
            if filename:
                data["data"] = {"filename": filename}

            response = self._send_request(data)
            return response and response.get("status") == "success"

        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
            return False
