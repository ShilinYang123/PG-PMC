#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC智能追踪系统 - 主应用类
"""

from typing import Optional

from src.ai.intelligent_scheduler import IntelligentScheduler
from src.ai.warning_system import WarningSystem
from src.config.settings import Settings
from src.database.connector import DatabaseConnector
from src.iot.device_manager import IoTDeviceManager
from src.ui.dashboard_interface import DashboardInterface
from src.utils.logger import get_logger


class PMCTrackingSystem:
    """PMC智能追踪系统主应用类"""

    def __init__(self, settings: Settings, dev_mode: bool = False):
        """初始化PMC智能追踪系统

        Args:
            settings: 配置对象
            dev_mode: 是否为开发模式
        """
        self.settings = settings
        self.dev_mode = dev_mode
        self.logger = get_logger(self.__class__.__name__)

        # 核心组件
        self.database_connector: Optional[DatabaseConnector] = None
        self.intelligent_scheduler: Optional[IntelligentScheduler] = None
        self.warning_system: Optional[WarningSystem] = None
        self.iot_device_manager: Optional[IoTDeviceManager] = None
        self.dashboard_interface: Optional[DashboardInterface] = None

        # 初始化标志
        self._initialized = False

    def initialize(self) -> bool:
        """初始化所有组件

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化PMC智能追踪系统组件...")

            # 初始化数据库连接器
            self.logger.info("初始化数据库连接器...")
            self.database_connector = DatabaseConnector(
                mysql_config=self.settings.database.mysql,
                mongodb_config=self.settings.database.mongodb,
                redis_config=self.settings.database.redis,
            )

            # 初始化智能调度器
            self.logger.info("初始化智能调度器...")
            self.intelligent_scheduler = IntelligentScheduler(
                tensorflow_config=self.settings.ai.tensorflow,
                pytorch_config=self.settings.ai.pytorch,
            )

            # 初始化预警系统
            self.logger.info("初始化预警系统...")
            self.warning_system = WarningSystem(
                scheduler=self.intelligent_scheduler,
                database=self.database_connector,
            )

            # 初始化IoT设备管理器
            self.logger.info("初始化IoT设备管理器...")
            self.iot_device_manager = IoTDeviceManager(
                mqtt_config=self.settings.iot_devices.mqtt,
                database=self.database_connector,
            )

            # 初始化仪表板界面
            self.logger.info("初始化仪表板界面...")
            self.dashboard_interface = DashboardInterface(
                scheduler=self.intelligent_scheduler,
                warning_system=self.warning_system,
                iot_manager=self.iot_device_manager,
                dev_mode=self.dev_mode,
            )

            self._initialized = True
            self.logger.info("✅ PMC智能追踪系统初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}")
            return False

    def test_database_connection(self) -> bool:
        """测试数据库连接

        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not self.database_connector:
                self.database_connector = DatabaseConnector(
                    mysql_config=self.settings.database.mysql,
                    mongodb_config=self.settings.database.mongodb,
                    redis_config=self.settings.database.redis,
                )

            return self.database_connector.test_connection()

        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False

    def run(self):
        """运行PMC智能追踪系统"""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("PMC智能追踪系统初始化失败")

        try:
            self.logger.info("🎯 PG-PMC智能追踪系统已启动")
            self.logger.info("📊 系统正在监控生产状态，提供智能调度和预警服务")

            # 启动仪表板界面
            self.dashboard_interface.start()

        except KeyboardInterrupt:
            self.logger.info("用户中断操作")
        except Exception as e:
            self.logger.error(f"运行时错误: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理资源...")

        if self.database_connector:
            self.database_connector.disconnect()

        if self.iot_device_manager:
            self.iot_device_manager.stop()

        if self.dashboard_interface:
            self.dashboard_interface.stop()

        self.logger.info("资源清理完成")

    def initialize_database(self) -> bool:
        """初始化数据库

        Returns:
            bool: 数据库初始化是否成功
        """
        try:
            if not self.database_connector:
                self.database_connector = DatabaseConnector(
                    mysql_config=self.settings.database.mysql,
                    mongodb_config=self.settings.database.mongodb,
                    redis_config=self.settings.database.redis,
                )

            return self.database_connector.initialize_database()

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            return False
