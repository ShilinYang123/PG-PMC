#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置同步模块
用于在不同环境和服务之间同步配置
"""

import os
import json
import yaml
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .config_manager import get_config_manager
from .config_validator import ConfigValidator
from .path_manager import get_path_manager


class SyncStatus(Enum):
    """同步状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncDirection(Enum):
    """同步方向枚举"""
    PUSH = "push"  # 推送到目标
    PULL = "pull"  # 从目标拉取
    BIDIRECTIONAL = "bidirectional"  # 双向同步


@dataclass
class SyncTarget:
    """同步目标配置"""
    name: str
    type: str  # 'file', 'database', 'redis', 'api', 'git'
    connection: Dict[str, Any]
    path: str
    enabled: bool = True
    priority: int = 0
    filters: List[str] = None  # 配置段过滤器
    transforms: Dict[str, str] = None  # 配置转换规则


@dataclass
class SyncRecord:
    """同步记录"""
    id: str
    target_name: str
    direction: SyncDirection
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    changes_count: int = 0
    config_hash: Optional[str] = None
    metadata: Dict[str, Any] = None


class ConfigSyncManager:
    """配置同步管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.validator = ConfigValidator()
        self.path_manager = get_path_manager()
        
        self.sync_targets: Dict[str, SyncTarget] = {}
        self.sync_history: List[SyncRecord] = []
        self.sync_lock = asyncio.Lock()
        
        # 同步配置
        self.sync_config_file = Path('config/sync_config.yaml')
        self.sync_history_file = Path('config/sync_history.json')
        
        # 加载同步配置
        self._load_sync_config()
        self._load_sync_history()
    
    def _load_sync_config(self):
        """加载同步配置"""
        if self.sync_config_file.exists():
            try:
                with open(self.sync_config_file, 'r', encoding='utf-8') as f:
                    sync_config = yaml.safe_load(f)
                
                for target_config in sync_config.get('targets', []):
                    target = SyncTarget(**target_config)
                    self.sync_targets[target.name] = target
                    
            except Exception as e:
                print(f"❌ 加载同步配置失败: {e}")
    
    def _load_sync_history(self):
        """加载同步历史"""
        if self.sync_history_file.exists():
            try:
                with open(self.sync_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                for record_data in history_data:
                    record = SyncRecord(
                        id=record_data['id'],
                        target_name=record_data['target_name'],
                        direction=SyncDirection(record_data['direction']),
                        status=SyncStatus(record_data['status']),
                        started_at=datetime.fromisoformat(record_data['started_at']),
                        completed_at=datetime.fromisoformat(record_data['completed_at']) if record_data.get('completed_at') else None,
                        error_message=record_data.get('error_message'),
                        changes_count=record_data.get('changes_count', 0),
                        config_hash=record_data.get('config_hash'),
                        metadata=record_data.get('metadata', {})
                    )
                    self.sync_history.append(record)
                    
            except Exception as e:
                print(f"❌ 加载同步历史失败: {e}")
    
    def _save_sync_config(self):
        """保存同步配置"""
        try:
            self.sync_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            sync_config = {
                'targets': [asdict(target) for target in self.sync_targets.values()]
            }
            
            with open(self.sync_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(sync_config, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            print(f"❌ 保存同步配置失败: {e}")
    
    def _save_sync_history(self):
        """保存同步历史"""
        try:
            self.sync_history_file.parent.mkdir(parents=True, exist_ok=True)
            
            history_data = []
            for record in self.sync_history[-100:]:  # 只保留最近100条记录
                record_dict = asdict(record)
                record_dict['direction'] = record.direction.value
                record_dict['status'] = record.status.value
                record_dict['started_at'] = record.started_at.isoformat()
                if record.completed_at:
                    record_dict['completed_at'] = record.completed_at.isoformat()
                history_data.append(record_dict)
            
            with open(self.sync_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ 保存同步历史失败: {e}")
    
    def add_sync_target(self, target: SyncTarget):
        """添加同步目标"""
        self.sync_targets[target.name] = target
        self._save_sync_config()
        print(f"✅ 添加同步目标: {target.name}")
    
    def remove_sync_target(self, target_name: str):
        """移除同步目标"""
        if target_name in self.sync_targets:
            del self.sync_targets[target_name]
            self._save_sync_config()
            print(f"✅ 移除同步目标: {target_name}")
        else:
            print(f"❌ 同步目标不存在: {target_name}")
    
    def get_sync_targets(self) -> Dict[str, SyncTarget]:
        """获取所有同步目标"""
        return self.sync_targets.copy()
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def _filter_config(self, config: Dict[str, Any], filters: List[str]) -> Dict[str, Any]:
        """根据过滤器筛选配置"""
        if not filters:
            return config
        
        filtered_config = {}
        for filter_path in filters:
            keys = filter_path.split('.')
            current = config
            target = filtered_config
            
            for i, key in enumerate(keys):
                if key in current:
                    if i == len(keys) - 1:
                        target[key] = current[key]
                    else:
                        if key not in target:
                            target[key] = {}
                        target = target[key]
                        current = current[key]
        
        return filtered_config
    
    def _transform_config(self, config: Dict[str, Any], transforms: Dict[str, str]) -> Dict[str, Any]:
        """根据转换规则转换配置"""
        if not transforms:
            return config
        
        # 这里可以实现复杂的配置转换逻辑
        # 例如：重命名键、转换值格式等
        transformed_config = config.copy()
        
        for source_path, target_path in transforms.items():
            # 简单的键重命名示例
            if source_path in transformed_config:
                value = transformed_config.pop(source_path)
                transformed_config[target_path] = value
        
        return transformed_config
    
    async def sync_to_file(self, target: SyncTarget, config: Dict[str, Any]) -> bool:
        """同步配置到文件"""
        try:
            file_path = Path(target.path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据文件扩展名选择格式
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                # 默认使用YAML格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            print(f"❌ 同步到文件失败: {e}")
            return False
    
    async def sync_from_file(self, target: SyncTarget) -> Optional[Dict[str, Any]]:
        """从文件同步配置"""
        try:
            file_path = Path(target.path)
            
            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                return None
            
            # 根据文件扩展名选择解析方式
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 默认尝试YAML格式
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            
        except Exception as e:
            print(f"❌ 从文件同步失败: {e}")
            return None
    
    async def sync_to_git(self, target: SyncTarget, config: Dict[str, Any]) -> bool:
        """同步配置到Git仓库"""
        try:
            # 这里可以实现Git同步逻辑
            # 例如：提交配置文件到Git仓库
            
            connection = target.connection
            repo_url = connection.get('repo_url')
            branch = connection.get('branch', 'main')
            
            # 实现Git推送逻辑
            print(f"🔄 同步配置到Git仓库: {repo_url}")
            
            # 这里应该实现实际的Git操作
            # 例如使用GitPython库
            
            return True
            
        except Exception as e:
            print(f"❌ 同步到Git失败: {e}")
            return False
    
    async def sync_to_api(self, target: SyncTarget, config: Dict[str, Any]) -> bool:
        """通过API同步配置"""
        try:
            import aiohttp
            
            connection = target.connection
            url = connection.get('url')
            headers = connection.get('headers', {})
            auth = connection.get('auth')
            
            async with aiohttp.ClientSession() as session:
                if auth:
                    headers['Authorization'] = f"Bearer {auth.get('token')}"
                
                async with session.post(url, json=config, headers=headers) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(f"❌ API同步失败: {response.status} {await response.text()}")
                        return False
            
        except Exception as e:
            print(f"❌ API同步失败: {e}")
            return False
    
    async def sync_push(self, target_name: str) -> SyncRecord:
        """推送配置到目标"""
        async with self.sync_lock:
            record = SyncRecord(
                id=f"{target_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target_name=target_name,
                direction=SyncDirection.PUSH,
                status=SyncStatus.IN_PROGRESS,
                started_at=datetime.now()
            )
            
            try:
                target = self.sync_targets.get(target_name)
                if not target or not target.enabled:
                    raise ValueError(f"同步目标不存在或已禁用: {target_name}")
                
                # 获取当前配置
                config = self.config_manager.get_config()
                
                # 应用过滤器
                if target.filters:
                    config = self._filter_config(config, target.filters)
                
                # 应用转换规则
                if target.transforms:
                    config = self._transform_config(config, target.transforms)
                
                # 计算配置哈希
                record.config_hash = self._calculate_config_hash(config)
                
                # 根据目标类型执行同步
                success = False
                if target.type == 'file':
                    success = await self.sync_to_file(target, config)
                elif target.type == 'git':
                    success = await self.sync_to_git(target, config)
                elif target.type == 'api':
                    success = await self.sync_to_api(target, config)
                else:
                    raise ValueError(f"不支持的同步目标类型: {target.type}")
                
                if success:
                    record.status = SyncStatus.SUCCESS
                    record.changes_count = 1  # 简化处理
                    print(f"✅ 配置推送成功: {target_name}")
                else:
                    record.status = SyncStatus.FAILED
                    record.error_message = "同步操作失败"
                
            except Exception as e:
                record.status = SyncStatus.FAILED
                record.error_message = str(e)
                print(f"❌ 配置推送失败: {target_name} - {e}")
            
            finally:
                record.completed_at = datetime.now()
                self.sync_history.append(record)
                self._save_sync_history()
            
            return record
    
    async def sync_pull(self, target_name: str) -> SyncRecord:
        """从目标拉取配置"""
        async with self.sync_lock:
            record = SyncRecord(
                id=f"{target_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target_name=target_name,
                direction=SyncDirection.PULL,
                status=SyncStatus.IN_PROGRESS,
                started_at=datetime.now()
            )
            
            try:
                target = self.sync_targets.get(target_name)
                if not target or not target.enabled:
                    raise ValueError(f"同步目标不存在或已禁用: {target_name}")
                
                # 根据目标类型拉取配置
                config = None
                if target.type == 'file':
                    config = await self.sync_from_file(target)
                else:
                    raise ValueError(f"暂不支持从 {target.type} 类型拉取配置")
                
                if config is None:
                    raise ValueError("拉取配置失败")
                
                # 验证配置
                validation_result = self.validator.validate_config_data(config)
                if not validation_result['valid']:
                    raise ValueError(f"配置验证失败: {validation_result['errors']}")
                
                # 更新本地配置
                if target.filters:
                    # 只更新指定的配置段
                    current_config = self.config_manager.get_config()
                    for filter_path in target.filters:
                        keys = filter_path.split('.')
                        self._update_nested_config(current_config, keys, config)
                    self.config_manager.save_config(current_config)
                else:
                    # 更新整个配置
                    self.config_manager.save_config(config)
                
                record.status = SyncStatus.SUCCESS
                record.config_hash = self._calculate_config_hash(config)
                record.changes_count = 1  # 简化处理
                print(f"✅ 配置拉取成功: {target_name}")
                
            except Exception as e:
                record.status = SyncStatus.FAILED
                record.error_message = str(e)
                print(f"❌ 配置拉取失败: {target_name} - {e}")
            
            finally:
                record.completed_at = datetime.now()
                self.sync_history.append(record)
                self._save_sync_history()
            
            return record
    
    def _update_nested_config(self, config: Dict[str, Any], keys: List[str], value: Any):
        """更新嵌套配置"""
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    async def sync_all(self, direction: SyncDirection = SyncDirection.PUSH) -> List[SyncRecord]:
        """同步所有目标"""
        records = []
        
        # 按优先级排序
        sorted_targets = sorted(
            [(name, target) for name, target in self.sync_targets.items() if target.enabled],
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        for target_name, target in sorted_targets:
            try:
                if direction == SyncDirection.PUSH:
                    record = await self.sync_push(target_name)
                elif direction == SyncDirection.PULL:
                    record = await self.sync_pull(target_name)
                else:
                    # 双向同步：先拉取再推送
                    pull_record = await self.sync_pull(target_name)
                    push_record = await self.sync_push(target_name)
                    record = push_record  # 返回推送记录
                
                records.append(record)
                
            except Exception as e:
                print(f"❌ 同步目标失败: {target_name} - {e}")
        
        return records
    
    def get_sync_history(self, target_name: Optional[str] = None, 
                        limit: int = 50) -> List[SyncRecord]:
        """获取同步历史"""
        history = self.sync_history
        
        if target_name:
            history = [r for r in history if r.target_name == target_name]
        
        return sorted(history, key=lambda x: x.started_at, reverse=True)[:limit]
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        status = {
            'targets_count': len(self.sync_targets),
            'enabled_targets': len([t for t in self.sync_targets.values() if t.enabled]),
            'recent_syncs': len([r for r in self.sync_history if r.started_at > datetime.now() - timedelta(hours=24)]),
            'failed_syncs': len([r for r in self.sync_history if r.status == SyncStatus.FAILED and r.started_at > datetime.now() - timedelta(hours=24)]),
            'last_sync': None
        }
        
        if self.sync_history:
            last_sync = max(self.sync_history, key=lambda x: x.started_at)
            status['last_sync'] = {
                'target': last_sync.target_name,
                'status': last_sync.status.value,
                'time': last_sync.started_at.isoformat()
            }
        
        return status
    
    def cleanup_history(self, days: int = 30):
        """清理历史记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self.sync_history)
        
        self.sync_history = [r for r in self.sync_history if r.started_at > cutoff_date]
        
        cleaned_count = original_count - len(self.sync_history)
        if cleaned_count > 0:
            self._save_sync_history()
            print(f"✅ 清理了 {cleaned_count} 条历史记录")


# 全局同步管理器实例
_sync_manager = None


def get_sync_manager() -> ConfigSyncManager:
    """获取全局同步管理器实例"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = ConfigSyncManager()
    return _sync_manager


# 便捷函数
async def sync_config_to_target(target_name: str) -> SyncRecord:
    """同步配置到指定目标"""
    manager = get_sync_manager()
    return await manager.sync_push(target_name)


async def sync_config_from_target(target_name: str) -> SyncRecord:
    """从指定目标同步配置"""
    manager = get_sync_manager()
    return await manager.sync_pull(target_name)


async def sync_all_targets(direction: SyncDirection = SyncDirection.PUSH) -> List[SyncRecord]:
    """同步所有目标"""
    manager = get_sync_manager()
    return await manager.sync_all(direction)


if __name__ == '__main__':
    # 测试配置同步
    async def test_sync():
        manager = ConfigSyncManager()
        
        # 添加文件同步目标
        file_target = SyncTarget(
            name='backup_config',
            type='file',
            connection={},
            path='backup/config_backup.yaml',
            filters=['database', 'server']
        )
        
        manager.add_sync_target(file_target)
        
        # 执行同步
        record = await manager.sync_push('backup_config')
        print(f"同步结果: {record.status.value}")
        
        # 显示状态
        status = manager.get_sync_status()
        print(f"同步状态: {status}")
    
    asyncio.run(test_sync())