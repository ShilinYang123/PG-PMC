#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置管理模块
"""

from .config_manager import ConfigManager
from .environment import EnvironmentManager
from .settings import AISettings, CreoSettings, Settings, UISettings

__all__ = [
    "Settings",
    "CreoSettings",
    "AISettings",
    "UISettings",
    "ConfigManager",
    "EnvironmentManager",
]

__version__ = "1.0.0"
__author__ = "PG-Dev Team"
