#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 主应用类
"""

from typing import Optional

from src.ai.design_interpreter import DesignInterpreter
from src.ai.language_processor import LanguageProcessor
from src.config.settings import Settings
from src.creo.connector import CreoConnector
from src.geometry.creator import GeometryCreator
from src.ui.chat_interface import ChatInterface
from src.utils.logger import get_logger


class AIDesignAssistant:
    """AI设计助理主应用类"""

    def __init__(self, settings: Settings, dev_mode: bool = False):
        """初始化AI设计助理

        Args:
            settings: 配置对象
            dev_mode: 是否为开发模式
        """
        self.settings = settings
        self.dev_mode = dev_mode
        self.logger = get_logger(self.__class__.__name__)

        # 核心组件
        self.creo_connector: Optional[CreoConnector] = None
        self.language_processor: Optional[LanguageProcessor] = None
        self.design_interpreter: Optional[DesignInterpreter] = None
        self.geometry_creator: Optional[GeometryCreator] = None
        self.chat_interface: Optional[ChatInterface] = None

        # 初始化标志
        self._initialized = False

    def initialize(self) -> bool:
        """初始化所有组件

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化AI设计助理组件...")

            # 初始化Creo连接器
            self.logger.info("初始化Creo连接器...")
            self.creo_connector = CreoConnector(
                creo_path=self.settings.creo.installation_path,
                timeout=self.settings.creo.connection_timeout,
            )

            # 初始化语言处理器
            self.logger.info("初始化语言处理器...")
            self.language_processor = LanguageProcessor(
                api_key=self.settings.ai.openai_api_key,
                model=self.settings.ai.model_name,
            )

            # 初始化设计解释器
            self.logger.info("初始化设计解释器...")
            self.design_interpreter = DesignInterpreter(
                language_processor=self.language_processor,
                design_rules=self.settings.design.rules,
            )

            # 初始化几何创建器
            self.logger.info("初始化几何创建器...")
            self.geometry_creator = GeometryCreator(creo_connector=self.creo_connector)

            # 初始化聊天界面
            self.logger.info("初始化用户界面...")
            self.chat_interface = ChatInterface(
                design_interpreter=self.design_interpreter,
                geometry_creator=self.geometry_creator,
                dev_mode=self.dev_mode,
            )

            self._initialized = True
            self.logger.info("✅ AI设计助理初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}")
            return False

    def test_creo_connection(self) -> bool:
        """测试Creo连接

        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not self.creo_connector:
                self.creo_connector = CreoConnector(
                    creo_path=self.settings.creo.installation_path,
                    timeout=self.settings.creo.connection_timeout,
                )

            return self.creo_connector.test_connection()

        except Exception as e:
            self.logger.error(f"Creo连接测试失败: {e}")
            return False

    def run(self):
        """运行AI设计助理"""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("AI设计助理初始化失败")

        try:
            self.logger.info("🎯 PG-Dev AI设计助理已启动")
            self.logger.info("💬 请输入您的设计需求，我将帮您在Creo中创建3D模型")

            # 启动聊天界面
            self.chat_interface.start()

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

        if self.creo_connector:
            self.creo_connector.disconnect()

        if self.chat_interface:
            self.chat_interface.stop()

        self.logger.info("资源清理完成")
