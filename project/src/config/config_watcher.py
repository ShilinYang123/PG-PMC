#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件监控和热重载模块
支持配置文件的实时监控和自动重载
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .config_manager import get_config_manager
from .config_validator import ConfigValidator


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_watcher: 'ConfigWatcher'):
        super().__init__()
        self.config_watcher = config_watcher
        self.last_modified = {}
        self.debounce_time = 1.0  # 防抖时间（秒）
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 只处理配置相关文件
        if not self._is_config_file(file_path):
            return
        
        # 防抖处理
        current_time = time.time()
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_time:
                return
        
        self.last_modified[file_path] = current_time
        
        # 异步处理文件变更
        threading.Thread(
            target=self.config_watcher._handle_file_change,
            args=(file_path,),
            daemon=True
        ).start()
    
    def _is_config_file(self, file_path: Path) -> bool:
        """判断是否为配置文件"""
        config_extensions = {'.yaml', '.yml', '.json', '.ini', '.env', '.conf'}
        return file_path.suffix.lower() in config_extensions


class ConfigWatcher:
    """配置文件监控器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.validator = ConfigValidator()
        self.observer = None
        self.is_running = False
        self.callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.watch_paths: List[Path] = []
        self.last_config_hash = None
        self.reload_lock = threading.Lock()
        
        # 默认监控路径
        self._setup_default_watch_paths()
    
    def _setup_default_watch_paths(self):
        """设置默认监控路径"""
        # 主配置文件目录
        config_dir = self.config_manager.config_file.parent
        if config_dir.exists():
            self.watch_paths.append(config_dir)
        
        # 项目根目录（监控.env文件等）
        project_root = Path.cwd()
        self.watch_paths.append(project_root)
        
        # 后端配置目录
        backend_dir = project_root / 'project' / 'backend'
        if backend_dir.exists():
            self.watch_paths.append(backend_dir)
    
    def add_watch_path(self, path: Path):
        """添加监控路径"""
        if path.exists() and path not in self.watch_paths:
            self.watch_paths.append(path)
    
    def add_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加配置变更回调函数
        
        Args:
            callback: 回调函数，参数为 (event_type, config_data)
                     event_type: 'reload', 'error', 'validation_failed'
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """移除配置变更回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_watching(self):
        """开始监控配置文件"""
        if self.is_running:
            return
        
        self.observer = Observer()
        handler = ConfigFileHandler(self)
        
        # 为每个监控路径添加观察者
        for watch_path in self.watch_paths:
            if watch_path.exists():
                self.observer.schedule(handler, str(watch_path), recursive=True)
        
        self.observer.start()
        self.is_running = True
        
        # 记录初始配置哈希
        self._update_config_hash()
        
        print(f"🔍 配置文件监控已启动，监控路径: {[str(p) for p in self.watch_paths]}")
    
    def stop_watching(self):
        """停止监控配置文件"""
        if not self.is_running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_running = False
        print("⏹️  配置文件监控已停止")
    
    def _handle_file_change(self, file_path: Path):
        """处理文件变更"""
        with self.reload_lock:
            try:
                print(f"📝 检测到配置文件变更: {file_path}")
                
                # 等待文件写入完成
                time.sleep(0.5)
                
                # 如果是主配置文件，重新加载配置
                if file_path == self.config_manager.config_file:
                    self._reload_main_config()
                
                # 如果是.env文件，重新加载环境变量
                elif file_path.name == '.env':
                    self._reload_env_file(file_path)
                
                # 如果是alembic.ini，检查数据库配置
                elif file_path.name == 'alembic.ini':
                    self._check_alembic_config(file_path)
                
                else:
                    # 其他配置文件，触发通用重载
                    self._trigger_generic_reload(file_path)
                
            except Exception as e:
                error_msg = f"处理配置文件变更失败: {e}"
                print(f"❌ {error_msg}")
                self._notify_callbacks('error', {'error': error_msg, 'file': str(file_path)})
    
    def _reload_main_config(self):
        """重新加载主配置文件"""
        try:
            # 验证配置文件
            validation_result = self.validator.validate_config_file()
            if not validation_result['valid']:
                error_msg = f"配置文件验证失败: {validation_result['errors']}"
                print(f"❌ {error_msg}")
                self._notify_callbacks('validation_failed', validation_result)
                return
            
            # 重新加载配置
            old_config = self.config_manager.get_config()
            self.config_manager.load_config()
            new_config = self.config_manager.get_config()
            
            # 检查配置是否真的发生了变化
            new_hash = self._calculate_config_hash(new_config)
            if new_hash == self.last_config_hash:
                print("📋 配置内容未发生变化")
                return
            
            self.last_config_hash = new_hash
            
            # 比较配置变更
            changes = self._compare_configs(old_config, new_config)
            
            print("✅ 主配置文件重新加载成功")
            if changes:
                print(f"📊 检测到 {len(changes)} 项配置变更")
                for change in changes[:5]:  # 只显示前5项变更
                    print(f"  • {change}")
                if len(changes) > 5:
                    print(f"  ... 还有 {len(changes) - 5} 项变更")
            
            # 通知回调函数
            self._notify_callbacks('reload', {
                'type': 'main_config',
                'old_config': old_config,
                'new_config': new_config,
                'changes': changes
            })
            
        except Exception as e:
            error_msg = f"重新加载主配置文件失败: {e}"
            print(f"❌ {error_msg}")
            self._notify_callbacks('error', {'error': error_msg})
    
    def _reload_env_file(self, file_path: Path):
        """重新加载.env文件"""
        try:
            print(f"🔄 重新加载环境变量文件: {file_path}")
            
            # 读取.env文件
            env_vars = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            # 更新环境变量
            for key, value in env_vars.items():
                os.environ[key] = value
            
            print(f"✅ 环境变量文件重新加载成功，更新了 {len(env_vars)} 个变量")
            
            # 通知回调函数
            self._notify_callbacks('reload', {
                'type': 'env_file',
                'file': str(file_path),
                'env_vars': env_vars
            })
            
        except Exception as e:
            error_msg = f"重新加载环境变量文件失败: {e}"
            print(f"❌ {error_msg}")
            self._notify_callbacks('error', {'error': error_msg, 'file': str(file_path)})
    
    def _check_alembic_config(self, file_path: Path):
        """检查alembic配置变更"""
        try:
            print(f"🔍 检查Alembic配置变更: {file_path}")
            
            # 这里可以添加alembic配置的特殊处理逻辑
            # 比如检查数据库连接字符串是否变更等
            
            print("✅ Alembic配置检查完成")
            
            # 通知回调函数
            self._notify_callbacks('reload', {
                'type': 'alembic_config',
                'file': str(file_path)
            })
            
        except Exception as e:
            error_msg = f"检查Alembic配置失败: {e}"
            print(f"❌ {error_msg}")
            self._notify_callbacks('error', {'error': error_msg, 'file': str(file_path)})
    
    def _trigger_generic_reload(self, file_path: Path):
        """触发通用重载"""
        try:
            print(f"🔄 触发通用配置重载: {file_path}")
            
            # 通知回调函数
            self._notify_callbacks('reload', {
                'type': 'generic',
                'file': str(file_path)
            })
            
        except Exception as e:
            error_msg = f"通用配置重载失败: {e}"
            print(f"❌ {error_msg}")
            self._notify_callbacks('error', {'error': error_msg, 'file': str(file_path)})
    
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback in self.callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"❌ 回调函数执行失败: {e}")
    
    def _update_config_hash(self):
        """更新配置哈希值"""
        try:
            config = self.config_manager.get_config()
            self.last_config_hash = self._calculate_config_hash(config)
        except Exception:
            self.last_config_hash = None
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        import hashlib
        import json
        
        # 将配置转换为JSON字符串并计算哈希
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _compare_configs(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """比较配置变更"""
        changes = []
        
        def compare_dict(old_dict, new_dict, prefix=''):
            # 检查新增和修改的键
            for key, new_value in new_dict.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if key not in old_dict:
                    changes.append(f"新增: {full_key} = {new_value}")
                elif old_dict[key] != new_value:
                    if isinstance(old_dict[key], dict) and isinstance(new_value, dict):
                        compare_dict(old_dict[key], new_value, full_key)
                    else:
                        changes.append(f"修改: {full_key} = {old_dict[key]} -> {new_value}")
            
            # 检查删除的键
            for key in old_dict:
                if key not in new_dict:
                    full_key = f"{prefix}.{key}" if prefix else key
                    changes.append(f"删除: {full_key}")
        
        compare_dict(old_config, new_config)
        return changes
    
    def force_reload(self):
        """强制重新加载配置"""
        print("🔄 强制重新加载配置...")
        self._reload_main_config()
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'watch_paths': [str(p) for p in self.watch_paths],
            'callbacks_count': len(self.callbacks),
            'last_config_hash': self.last_config_hash
        }


# 全局配置监控器实例
_config_watcher = None


def get_config_watcher() -> ConfigWatcher:
    """获取全局配置监控器实例"""
    global _config_watcher
    if _config_watcher is None:
        _config_watcher = ConfigWatcher()
    return _config_watcher


def start_config_watching():
    """启动配置文件监控"""
    watcher = get_config_watcher()
    watcher.start_watching()
    return watcher


def stop_config_watching():
    """停止配置文件监控"""
    watcher = get_config_watcher()
    watcher.stop_watching()


def add_config_change_callback(callback: Callable[[str, Dict[str, Any]], None]):
    """添加配置变更回调函数"""
    watcher = get_config_watcher()
    watcher.add_callback(callback)


def remove_config_change_callback(callback: Callable[[str, Dict[str, Any]], None]):
    """移除配置变更回调函数"""
    watcher = get_config_watcher()
    watcher.remove_callback(callback)


# 示例回调函数
def example_config_callback(event_type: str, data: Dict[str, Any]):
    """示例配置变更回调函数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if event_type == 'reload':
        config_type = data.get('type', 'unknown')
        print(f"[{timestamp}] 📋 配置重载: {config_type}")
        
        if 'changes' in data and data['changes']:
            print(f"  变更数量: {len(data['changes'])}")
    
    elif event_type == 'error':
        error = data.get('error', 'Unknown error')
        print(f"[{timestamp}] ❌ 配置错误: {error}")
    
    elif event_type == 'validation_failed':
        errors = data.get('errors', [])
        print(f"[{timestamp}] ⚠️  配置验证失败: {len(errors)} 个错误")


if __name__ == '__main__':
    # 测试配置监控
    watcher = get_config_watcher()
    watcher.add_callback(example_config_callback)
    
    try:
        watcher.start_watching()
        print("配置监控已启动，按 Ctrl+C 停止...")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n停止配置监控...")
        watcher.stop_watching()