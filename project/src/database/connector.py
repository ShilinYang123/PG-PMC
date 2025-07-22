#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC智能追踪系统 - 数据库连接器
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.logger import get_logger


class DatabaseConnector:
    """PMC数据库连接器
    
    负责管理PMC系统的数据库连接和操作
    """
    
    def __init__(self, mysql_config=None, mongodb_config=None, redis_config=None):
        """初始化数据库连接器
        
        Args:
            mysql_config: MySQL配置
            mongodb_config: MongoDB配置  
            redis_config: Redis配置
        """
        self.logger = get_logger(self.__class__.__name__)
        
        # 使用SQLite作为默认数据库
        self.db_path = Path("data/pmc_database.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connection: Optional[sqlite3.Connection] = None
        self._connected = False
        
    def connect(self) -> bool:
        """连接到数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问
            self._connected = True
            
            # 创建基础表结构
            self._create_tables()
            
            self.logger.info("✅ 数据库连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            self._connected = False
            return False
    
    def _create_tables(self):
        """创建数据库表结构"""
        cursor = self.connection.cursor()
        
        # 项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planning',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # 生产计划表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS production_plans (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                plan_name TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan_data TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # 设备状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT
            )
        """)
        
        # 质量记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                batch_id TEXT,
                check_type TEXT,
                result TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        self.connection.commit()
        self.logger.info("数据库表结构创建完成")
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self._connected = False
            self.logger.info("数据库连接已断开")
    
    def test_connection(self) -> bool:
        """测试数据库连接
        
        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not self._connected:
                if not self.connect():
                    return False
            
            # 执行简单查询测试
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            self.logger.info("数据库连接测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """初始化数据库
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            if not self._connected:
                if not self.connect():
                    return False
            
            # 插入一些示例数据
            cursor = self.connection.cursor()
            
            # 检查是否已有数据
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # 插入示例项目
                sample_project = {
                    'id': 'sample_001',
                    'name': 'PMC系统示例项目',
                    'description': '用于演示PMC管理功能的示例项目',
                    'status': 'active',
                    'metadata': json.dumps({
                        'type': 'production',
                        'priority': 'high',
                        'team_size': 5
                    })
                }
                
                cursor.execute("""
                    INSERT INTO projects (id, name, description, status, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sample_project['id'],
                    sample_project['name'], 
                    sample_project['description'],
                    sample_project['status'],
                    sample_project['metadata']
                ))
                
                self.connection.commit()
                self.logger.info("示例数据插入完成")
            
            self.logger.info("✅ 数据库初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        try:
            if not self._connected:
                if not self.connect():
                    return []
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """执行更新操作
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._connected:
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"更新执行失败: {e}")
            return False