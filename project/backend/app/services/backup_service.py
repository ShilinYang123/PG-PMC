"""数据备份恢复服务

提供完整的数据备份和恢复功能：
- 数据库备份和恢复
- 文件系统备份
- 配置文件备份
- 增量备份和全量备份
- 备份文件管理和清理
- 备份验证和完整性检查
"""

import os
import json
import shutil
import zipfile
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import subprocess
import tempfile
from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from ..database import SessionLocal, engine
from ..core.config import settings
from ..core.exceptions import ValidationException, BusinessException
from .file_service import FileService


class BackupService:
    """备份恢复服务类"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else 'backups')
        self.temp_dir = Path(tempfile.gettempdir()) / 'pmc_backup_temp'
        self.file_service = FileService()
        
        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份类型配置
        self.backup_types = {
            'database': {'enabled': True, 'retention_days': 30},
            'files': {'enabled': True, 'retention_days': 7},
            'config': {'enabled': True, 'retention_days': 90},
            'logs': {'enabled': False, 'retention_days': 3}
        }
        
        # 数据库备份配置
        self.db_config = {
            'host': getattr(settings, 'DATABASE_HOST', 'localhost'),
            'port': getattr(settings, 'DATABASE_PORT', 5432),
            'database': getattr(settings, 'DATABASE_NAME', 'pmc_db'),
            'username': getattr(settings, 'DATABASE_USER', 'postgres'),
            'password': getattr(settings, 'DATABASE_PASSWORD', '')
        }
    
    def create_full_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        创建完整备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            Dict: 备份信息
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f'full_backup_{timestamp}'
            
            backup_info = {
                'backup_id': f'backup_{timestamp}',
                'backup_name': backup_name,
                'backup_type': 'full',
                'created_time': datetime.now(),
                'status': 'in_progress',
                'components': {},
                'file_path': None,
                'file_size': 0,
                'checksum': None
            }
            
            logger.info(f"开始创建完整备份: {backup_name}")
            
            # 创建临时备份目录
            temp_backup_dir = self.temp_dir / backup_name
            temp_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. 备份数据库
            if self.backup_types['database']['enabled']:
                db_backup_path = self._backup_database(temp_backup_dir)
                backup_info['components']['database'] = {
                    'status': 'completed' if db_backup_path else 'failed',
                    'file_path': str(db_backup_path) if db_backup_path else None,
                    'size': db_backup_path.stat().st_size if db_backup_path and db_backup_path.exists() else 0
                }
            
            # 2. 备份文件
            if self.backup_types['files']['enabled']:
                files_backup_path = self._backup_files(temp_backup_dir)
                backup_info['components']['files'] = {
                    'status': 'completed' if files_backup_path else 'failed',
                    'file_path': str(files_backup_path) if files_backup_path else None,
                    'size': files_backup_path.stat().st_size if files_backup_path and files_backup_path.exists() else 0
                }
            
            # 3. 备份配置
            if self.backup_types['config']['enabled']:
                config_backup_path = self._backup_config(temp_backup_dir)
                backup_info['components']['config'] = {
                    'status': 'completed' if config_backup_path else 'failed',
                    'file_path': str(config_backup_path) if config_backup_path else None,
                    'size': config_backup_path.stat().st_size if config_backup_path and config_backup_path.exists() else 0
                }
            
            # 4. 创建备份元数据
            metadata = {
                'backup_info': backup_info,
                'system_info': self._get_system_info(),
                'database_schema': self._get_database_schema()
            }
            
            metadata_file = temp_backup_dir / 'backup_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str, ensure_ascii=False)
            
            # 5. 压缩备份文件
            backup_archive = self.backup_dir / f'{backup_name}.zip'
            self._create_archive(temp_backup_dir, backup_archive)
            
            # 6. 计算校验和
            checksum = self._calculate_checksum(backup_archive)
            
            # 7. 更新备份信息
            backup_info.update({
                'status': 'completed',
                'file_path': str(backup_archive),
                'file_size': backup_archive.stat().st_size,
                'checksum': checksum
            })
            
            # 8. 保存备份记录
            self._save_backup_record(backup_info)
            
            # 9. 清理临时文件
            shutil.rmtree(temp_backup_dir, ignore_errors=True)
            
            logger.info(f"完整备份创建成功: {backup_name}, 大小: {backup_info['file_size']} 字节")
            return backup_info
            
        except Exception as e:
            logger.error(f"创建完整备份失败: {e}")
            # 清理临时文件
            if 'temp_backup_dir' in locals():
                shutil.rmtree(temp_backup_dir, ignore_errors=True)
            raise BusinessException(f"创建备份失败: {str(e)}")
    
    def create_incremental_backup(self, base_backup_id: str, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        创建增量备份
        
        Args:
            base_backup_id: 基础备份ID
            backup_name: 备份名称
            
        Returns:
            Dict: 备份信息
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f'incremental_backup_{timestamp}'
            
            # 获取基础备份信息
            base_backup = self._get_backup_record(base_backup_id)
            if not base_backup:
                raise ValidationException(f"基础备份不存在: {base_backup_id}")
            
            backup_info = {
                'backup_id': f'backup_{timestamp}',
                'backup_name': backup_name,
                'backup_type': 'incremental',
                'base_backup_id': base_backup_id,
                'created_time': datetime.now(),
                'status': 'in_progress',
                'components': {},
                'file_path': None,
                'file_size': 0,
                'checksum': None
            }
            
            logger.info(f"开始创建增量备份: {backup_name}, 基于: {base_backup_id}")
            
            # 创建临时备份目录
            temp_backup_dir = self.temp_dir / backup_name
            temp_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取基础备份时间
            base_time = base_backup['created_time']
            if isinstance(base_time, str):
                base_time = datetime.fromisoformat(base_time)
            
            # 1. 增量备份数据库
            if self.backup_types['database']['enabled']:
                db_backup_path = self._backup_database_incremental(temp_backup_dir, base_time)
                backup_info['components']['database'] = {
                    'status': 'completed' if db_backup_path else 'failed',
                    'file_path': str(db_backup_path) if db_backup_path else None,
                    'size': db_backup_path.stat().st_size if db_backup_path and db_backup_path.exists() else 0
                }
            
            # 2. 增量备份文件
            if self.backup_types['files']['enabled']:
                files_backup_path = self._backup_files_incremental(temp_backup_dir, base_time)
                backup_info['components']['files'] = {
                    'status': 'completed' if files_backup_path else 'failed',
                    'file_path': str(files_backup_path) if files_backup_path else None,
                    'size': files_backup_path.stat().st_size if files_backup_path and files_backup_path.exists() else 0
                }
            
            # 3. 创建备份元数据
            metadata = {
                'backup_info': backup_info,
                'base_backup_info': base_backup,
                'system_info': self._get_system_info()
            }
            
            metadata_file = temp_backup_dir / 'backup_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str, ensure_ascii=False)
            
            # 4. 压缩备份文件
            backup_archive = self.backup_dir / f'{backup_name}.zip'
            self._create_archive(temp_backup_dir, backup_archive)
            
            # 5. 计算校验和
            checksum = self._calculate_checksum(backup_archive)
            
            # 6. 更新备份信息
            backup_info.update({
                'status': 'completed',
                'file_path': str(backup_archive),
                'file_size': backup_archive.stat().st_size,
                'checksum': checksum
            })
            
            # 7. 保存备份记录
            self._save_backup_record(backup_info)
            
            # 8. 清理临时文件
            shutil.rmtree(temp_backup_dir, ignore_errors=True)
            
            logger.info(f"增量备份创建成功: {backup_name}, 大小: {backup_info['file_size']} 字节")
            return backup_info
            
        except Exception as e:
            logger.error(f"创建增量备份失败: {e}")
            # 清理临时文件
            if 'temp_backup_dir' in locals():
                shutil.rmtree(temp_backup_dir, ignore_errors=True)
            raise BusinessException(f"创建增量备份失败: {str(e)}")
    
    def restore_backup(self, backup_id: str, restore_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        恢复备份
        
        Args:
            backup_id: 备份ID
            restore_options: 恢复选项
            
        Returns:
            Dict: 恢复结果
        """
        try:
            restore_options = restore_options or {}
            
            # 获取备份信息
            backup_info = self._get_backup_record(backup_id)
            if not backup_info:
                raise ValidationException(f"备份不存在: {backup_id}")
            
            backup_file = Path(backup_info['file_path'])
            if not backup_file.exists():
                raise ValidationException(f"备份文件不存在: {backup_file}")
            
            logger.info(f"开始恢复备份: {backup_id}")
            
            restore_result = {
                'backup_id': backup_id,
                'restore_time': datetime.now(),
                'status': 'in_progress',
                'components': {},
                'errors': []
            }
            
            # 创建临时恢复目录
            temp_restore_dir = self.temp_dir / f'restore_{backup_id}'
            temp_restore_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. 解压备份文件
            self._extract_archive(backup_file, temp_restore_dir)
            
            # 2. 读取备份元数据
            metadata_file = temp_restore_dir / 'backup_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # 3. 恢复数据库
            if restore_options.get('restore_database', True) and 'database' in backup_info.get('components', {}):
                try:
                    self._restore_database(temp_restore_dir)
                    restore_result['components']['database'] = {'status': 'completed'}
                except Exception as e:
                    restore_result['components']['database'] = {'status': 'failed', 'error': str(e)}
                    restore_result['errors'].append(f"数据库恢复失败: {e}")
            
            # 4. 恢复文件
            if restore_options.get('restore_files', True) and 'files' in backup_info.get('components', {}):
                try:
                    self._restore_files(temp_restore_dir)
                    restore_result['components']['files'] = {'status': 'completed'}
                except Exception as e:
                    restore_result['components']['files'] = {'status': 'failed', 'error': str(e)}
                    restore_result['errors'].append(f"文件恢复失败: {e}")
            
            # 5. 恢复配置
            if restore_options.get('restore_config', True) and 'config' in backup_info.get('components', {}):
                try:
                    self._restore_config(temp_restore_dir)
                    restore_result['components']['config'] = {'status': 'completed'}
                except Exception as e:
                    restore_result['components']['config'] = {'status': 'failed', 'error': str(e)}
                    restore_result['errors'].append(f"配置恢复失败: {e}")
            
            # 6. 更新恢复状态
            if restore_result['errors']:
                restore_result['status'] = 'completed_with_errors'
            else:
                restore_result['status'] = 'completed'
            
            # 7. 保存恢复记录
            self._save_restore_record(restore_result)
            
            # 8. 清理临时文件
            shutil.rmtree(temp_restore_dir, ignore_errors=True)
            
            logger.info(f"备份恢复完成: {backup_id}, 状态: {restore_result['status']}")
            return restore_result
            
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            # 清理临时文件
            if 'temp_restore_dir' in locals():
                shutil.rmtree(temp_restore_dir, ignore_errors=True)
            raise BusinessException(f"恢复备份失败: {str(e)}")
    
    def list_backups(self, backup_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出备份记录
        
        Args:
            backup_type: 备份类型过滤
            limit: 返回数量限制
            
        Returns:
            List: 备份记录列表
        """
        try:
            backup_records = self._get_backup_records(backup_type, limit)
            return backup_records
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            raise BusinessException(f"获取备份列表失败: {str(e)}")
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        删除备份
        
        Args:
            backup_id: 备份ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取备份信息
            backup_info = self._get_backup_record(backup_id)
            if not backup_info:
                return False
            
            # 删除备份文件
            backup_file = Path(backup_info['file_path'])
            if backup_file.exists():
                backup_file.unlink()
            
            # 删除备份记录
            self._delete_backup_record(backup_id)
            
            logger.info(f"备份删除成功: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    def cleanup_old_backups(self) -> Dict[str, int]:
        """
        清理过期备份
        
        Returns:
            Dict: 清理统计
        """
        try:
            cleanup_stats = {'deleted_count': 0, 'freed_space': 0}
            
            for backup_type, config in self.backup_types.items():
                if not config['enabled']:
                    continue
                
                retention_days = config['retention_days']
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                # 获取过期备份
                expired_backups = self._get_expired_backups(backup_type, cutoff_date)
                
                for backup in expired_backups:
                    backup_file = Path(backup['file_path'])
                    if backup_file.exists():
                        file_size = backup_file.stat().st_size
                        backup_file.unlink()
                        cleanup_stats['freed_space'] += file_size
                    
                    self._delete_backup_record(backup['backup_id'])
                    cleanup_stats['deleted_count'] += 1
            
            logger.info(
                f"备份清理完成: 删除 {cleanup_stats['deleted_count']} 个备份, "
                f"释放空间 {cleanup_stats['freed_space']} 字节"
            )
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"清理备份失败: {e}")
            return {'deleted_count': 0, 'freed_space': 0}
    
    def verify_backup(self, backup_id: str, deep_check: bool = False) -> Dict[str, Any]:
        """
        验证备份完整性
        
        Args:
            backup_id: 备份ID
            deep_check: 是否进行深度检查
            
        Returns:
            Dict: 验证结果
        """
        try:
            # 获取备份信息
            backup_info = self._get_backup_record(backup_id)
            if not backup_info:
                raise ValidationException(f"备份不存在: {backup_id}")
            
            backup_file = Path(backup_info['file_path'])
            if not backup_file.exists():
                return {
                    'backup_id': backup_id,
                    'status': 'failed',
                    'error': '备份文件不存在'
                }
            
            verification_result = {
                'backup_id': backup_id,
                'status': 'valid',
                'file_size': 0,
                'checksum': None,
                'verified_time': datetime.now(),
                'checks': {
                    'file_exists': True,
                    'size_match': False,
                    'checksum_match': False,
                    'archive_integrity': False,
                    'content_validation': False
                },
                'errors': []
            }
            
            # 验证文件大小
            actual_size = backup_file.stat().st_size
            expected_size = backup_info.get('file_size', 0)
            verification_result['file_size'] = actual_size
            
            if actual_size == expected_size:
                verification_result['checks']['size_match'] = True
            else:
                verification_result['errors'].append(f'文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}')
            
            # 验证校验和
            actual_checksum = self._calculate_checksum(backup_file)
            verification_result['checksum'] = actual_checksum
            expected_checksum = backup_info.get('checksum')
            
            if expected_checksum and actual_checksum == expected_checksum:
                verification_result['checks']['checksum_match'] = True
            elif expected_checksum:
                verification_result['errors'].append(f'校验和不匹配: 期望 {expected_checksum}, 实际 {actual_checksum}')
            
            # 验证压缩文件完整性
            try:
                with zipfile.ZipFile(backup_file, 'r') as zip_file:
                    test_result = zip_file.testzip()
                    if test_result is None:
                        verification_result['checks']['archive_integrity'] = True
                    else:
                        verification_result['errors'].append(f'压缩文件损坏: {test_result}')
            except Exception as e:
                verification_result['errors'].append(f'压缩文件损坏: {e}')
            
            # 深度检查
            if deep_check:
                content_check = self._deep_content_validation(backup_file, backup_info)
                verification_result['checks']['content_validation'] = content_check['valid']
                if not content_check['valid']:
                    verification_result['errors'].extend(content_check['errors'])
                verification_result['content_details'] = content_check.get('details', {})
            
            # 确定最终状态
            if verification_result['errors']:
                verification_result['status'] = 'failed'
            
            return verification_result
            
        except Exception as e:
            logger.error(f"验证备份失败: {e}")
            return {
                'backup_id': backup_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_backup_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取备份统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 统计信息
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_backups = self._get_backup_records()
            
            # 过滤指定时间范围内的备份
            recent_backups = []
            for backup in all_backups:
                created_time = backup.get('created_time')
                if isinstance(created_time, str):
                    created_time = datetime.fromisoformat(created_time)
                if created_time and created_time >= cutoff_date:
                    recent_backups.append(backup)
            
            # 统计信息
            stats = {
                'period_days': days,
                'total_backups': len(recent_backups),
                'backup_types': {},
                'total_size': 0,
                'success_rate': 0,
                'average_size': 0,
                'largest_backup': None,
                'smallest_backup': None,
                'daily_counts': {},
                'storage_usage': self._get_storage_usage()
            }
            
            if not recent_backups:
                return stats
            
            # 按类型统计
            type_stats = {}
            successful_backups = 0
            sizes = []
            
            for backup in recent_backups:
                backup_type = backup.get('backup_type', 'unknown')
                if backup_type not in type_stats:
                    type_stats[backup_type] = {'count': 0, 'size': 0}
                
                type_stats[backup_type]['count'] += 1
                
                file_size = backup.get('file_size', 0)
                type_stats[backup_type]['size'] += file_size
                stats['total_size'] += file_size
                sizes.append(file_size)
                
                if backup.get('status') == 'completed':
                    successful_backups += 1
                
                # 按日期统计
                created_time = backup.get('created_time')
                if isinstance(created_time, str):
                    created_time = datetime.fromisoformat(created_time)
                if created_time:
                    date_key = created_time.strftime('%Y-%m-%d')
                    stats['daily_counts'][date_key] = stats['daily_counts'].get(date_key, 0) + 1
            
            stats['backup_types'] = type_stats
            stats['success_rate'] = (successful_backups / len(recent_backups)) * 100 if recent_backups else 0
            stats['average_size'] = sum(sizes) / len(sizes) if sizes else 0
            
            if sizes:
                largest_size = max(sizes)
                smallest_size = min(sizes)
                stats['largest_backup'] = next((b for b in recent_backups if b.get('file_size') == largest_size), None)
                stats['smallest_backup'] = next((b for b in recent_backups if b.get('file_size') == smallest_size), None)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取备份统计失败: {e}")
            return {'error': str(e)}
    
    def manage_backup_file(self, backup_id: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        管理备份文件
        
        Args:
            backup_id: 备份ID
            action: 操作类型 (rename, move, copy, compress)
            **kwargs: 操作参数
            
        Returns:
            Dict: 操作结果
        """
        try:
            backup_info = self._get_backup_record(backup_id)
            if not backup_info:
                raise ValidationException(f"备份不存在: {backup_id}")
            
            backup_file = Path(backup_info['file_path'])
            if not backup_file.exists():
                raise ValidationException("备份文件不存在")
            
            result = {'backup_id': backup_id, 'action': action, 'status': 'success'}
            
            if action == 'rename':
                new_name = kwargs.get('new_name')
                if not new_name:
                    raise ValidationException("新名称不能为空")
                
                new_path = backup_file.parent / f"{new_name}.zip"
                backup_file.rename(new_path)
                
                # 更新备份记录
                backup_info['file_path'] = str(new_path)
                backup_info['backup_name'] = new_name
                self._update_backup_record(backup_info)
                
                result['new_path'] = str(new_path)
                
            elif action == 'move':
                target_dir = Path(kwargs.get('target_directory', ''))
                if not target_dir or not target_dir.exists():
                    raise ValidationException("目标目录无效")
                
                new_path = target_dir / backup_file.name
                shutil.move(str(backup_file), str(new_path))
                
                # 更新备份记录
                backup_info['file_path'] = str(new_path)
                self._update_backup_record(backup_info)
                
                result['new_path'] = str(new_path)
                
            elif action == 'copy':
                target_path = kwargs.get('target_path')
                if not target_path:
                    raise ValidationException("目标路径不能为空")
                
                target_path = Path(target_path)
                shutil.copy2(backup_file, target_path)
                
                result['copy_path'] = str(target_path)
                
            elif action == 'compress':
                # 重新压缩以优化大小
                optimized_path = self._optimize_backup_compression(backup_file)
                if optimized_path and optimized_path != backup_file:
                    # 替换原文件
                    backup_file.unlink()
                    optimized_path.rename(backup_file)
                    
                    # 更新备份记录
                    backup_info['file_size'] = backup_file.stat().st_size
                    backup_info['checksum'] = self._calculate_checksum(backup_file)
                    self._update_backup_record(backup_info)
                    
                    result['size_reduction'] = kwargs.get('original_size', 0) - backup_info['file_size']
                
            else:
                raise ValidationException(f"不支持的操作: {action}")
            
            logger.info(f"备份文件管理操作完成: {action} - {backup_id}")
            return result
            
        except Exception as e:
            logger.error(f"备份文件管理失败: {e}")
            return {'backup_id': backup_id, 'action': action, 'status': 'failed', 'error': str(e)}
    
    def get_backup_history(self, backup_id: str) -> Dict[str, Any]:
        """
        获取备份历史记录
        
        Args:
            backup_id: 备份ID
            
        Returns:
            Dict: 历史记录
        """
        try:
            backup_info = self._get_backup_record(backup_id)
            if not backup_info:
                raise ValidationException(f"备份不存在: {backup_id}")
            
            # 获取恢复记录
            restore_records = self._get_restore_records_for_backup(backup_id)
            
            # 获取验证记录
            verification_records = self._get_verification_records(backup_id)
            
            # 获取操作记录
            operation_records = self._get_operation_records(backup_id)
            
            history = {
                'backup_info': backup_info,
                'restore_history': restore_records,
                'verification_history': verification_records,
                'operation_history': operation_records,
                'timeline': self._build_backup_timeline(backup_info, restore_records, verification_records, operation_records)
            }
            
            return history
            
        except Exception as e:
            logger.error(f"获取备份历史失败: {e}")
            return {'error': str(e)}
    
    def search_backups(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜索备份
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List: 匹配的备份列表
        """
        try:
            all_backups = self._get_backup_records()
            filtered_backups = []
            
            for backup in all_backups:
                match = True
                
                # 按备份类型过滤
                if 'backup_type' in criteria:
                    if backup.get('backup_type') != criteria['backup_type']:
                        match = False
                
                # 按状态过滤
                if 'status' in criteria:
                    if backup.get('status') != criteria['status']:
                        match = False
                
                # 按时间范围过滤
                if 'date_from' in criteria or 'date_to' in criteria:
                    created_time = backup.get('created_time')
                    if isinstance(created_time, str):
                        created_time = datetime.fromisoformat(created_time)
                    
                    if 'date_from' in criteria:
                        date_from = datetime.fromisoformat(criteria['date_from']) if isinstance(criteria['date_from'], str) else criteria['date_from']
                        if created_time < date_from:
                            match = False
                    
                    if 'date_to' in criteria:
                        date_to = datetime.fromisoformat(criteria['date_to']) if isinstance(criteria['date_to'], str) else criteria['date_to']
                        if created_time > date_to:
                            match = False
                
                # 按大小范围过滤
                if 'size_min' in criteria:
                    if backup.get('file_size', 0) < criteria['size_min']:
                        match = False
                
                if 'size_max' in criteria:
                    if backup.get('file_size', 0) > criteria['size_max']:
                        match = False
                
                # 按名称模糊匹配
                if 'name_pattern' in criteria:
                    pattern = criteria['name_pattern'].lower()
                    backup_name = backup.get('backup_name', '').lower()
                    if pattern not in backup_name:
                        match = False
                
                if match:
                    filtered_backups.append(backup)
            
            # 排序
            sort_by = criteria.get('sort_by', 'created_time')
            reverse = criteria.get('sort_desc', True)
            
            if sort_by in ['created_time', 'file_size', 'backup_name']:
                filtered_backups.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
            
            # 限制结果数量
            limit = criteria.get('limit', 100)
            return filtered_backups[:limit]
            
        except Exception as e:
            logger.error(f"搜索备份失败: {e}")
            return []
    
    def export_backup_metadata(self, backup_ids: Optional[List[str]] = None, format: str = 'json') -> Dict[str, Any]:
        """
        导出备份元数据
        
        Args:
            backup_ids: 备份ID列表，None表示导出所有
            format: 导出格式 (json, csv)
            
        Returns:
            Dict: 导出结果
        """
        try:
            if backup_ids:
                backups = [self._get_backup_record(bid) for bid in backup_ids]
                backups = [b for b in backups if b is not None]
            else:
                backups = self._get_backup_records()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = self.backup_dir / f'backup_metadata_export_{timestamp}.{format}'
            
            if format == 'json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'export_time': datetime.now().isoformat(),
                        'total_backups': len(backups),
                        'backups': backups
                    }, f, indent=2, default=str, ensure_ascii=False)
            
            elif format == 'csv':
                import csv
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    if backups:
                        fieldnames = ['backup_id', 'backup_name', 'backup_type', 'created_time', 'status', 'file_size', 'checksum']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for backup in backups:
                            row = {field: backup.get(field, '') for field in fieldnames}
                            writer.writerow(row)
            
            return {
                'status': 'success',
                'export_file': str(export_file),
                'exported_count': len(backups),
                'format': format
            }
            
        except Exception as e:
            logger.error(f"导出备份元数据失败: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    # 私有方法
    def _backup_database(self, backup_dir: Path) -> Optional[Path]:
        """备份数据库"""
        try:
            db_backup_file = backup_dir / 'database_backup.sql'
            
            # 使用pg_dump备份PostgreSQL数据库
            if hasattr(settings, 'DATABASE_URL') and 'postgresql' in settings.DATABASE_URL:
                cmd = [
                    'pg_dump',
                    '-h', self.db_config['host'],
                    '-p', str(self.db_config['port']),
                    '-U', self.db_config['username'],
                    '-d', self.db_config['database'],
                    '-f', str(db_backup_file),
                    '--no-password'
                ]
                
                env = os.environ.copy()
                env['PGPASSWORD'] = self.db_config['password']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"数据库备份失败: {result.stderr}")
                    return None
            else:
                # SQLite备份
                db_path = getattr(settings, 'DATABASE_URL', '').replace('sqlite:///', '')
                if db_path and Path(db_path).exists():
                    shutil.copy2(db_path, db_backup_file)
                else:
                    # 使用SQLAlchemy导出数据
                    self._export_database_data(db_backup_file)
            
            return db_backup_file if db_backup_file.exists() else None
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return None
    
    def _backup_files(self, backup_dir: Path) -> Optional[Path]:
        """备份文件"""
        try:
            files_backup_file = backup_dir / 'files_backup.zip'
            
            # 备份上传文件目录
            upload_dir = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else 'uploads')
            if upload_dir.exists():
                with zipfile.ZipFile(files_backup_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in upload_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(upload_dir.parent)
                            zip_file.write(file_path, arcname)
            
            return files_backup_file if files_backup_file.exists() else None
            
        except Exception as e:
            logger.error(f"文件备份失败: {e}")
            return None
    
    def _backup_config(self, backup_dir: Path) -> Optional[Path]:
        """备份配置"""
        try:
            config_backup_file = backup_dir / 'config_backup.zip'
            
            with zipfile.ZipFile(config_backup_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 备份配置文件
                config_files = [
                    'config.py',
                    '.env',
                    'requirements.txt',
                    'docker-compose.yml',
                    'Dockerfile'
                ]
                
                project_root = Path.cwd()
                for config_file in config_files:
                    file_path = project_root / config_file
                    if file_path.exists():
                        zip_file.write(file_path, config_file)
                
                # 备份应用配置目录
                app_config_dir = project_root / 'backend' / 'app' / 'core'
                if app_config_dir.exists():
                    for file_path in app_config_dir.rglob('*.py'):
                        if file_path.is_file():
                            arcname = f'app_config/{file_path.relative_to(app_config_dir)}'
                            zip_file.write(file_path, arcname)
            
            return config_backup_file if config_backup_file.exists() else None
            
        except Exception as e:
            logger.error(f"配置备份失败: {e}")
            return None
    
    def _backup_database_incremental(self, backup_dir: Path, since_time: datetime) -> Optional[Path]:
        """增量备份数据库"""
        try:
            # 对于增量备份，这里简化为备份有更新时间字段的表的增量数据
            db_backup_file = backup_dir / 'database_incremental.sql'
            
            # 这里可以根据具体需求实现增量备份逻辑
            # 例如：只备份自since_time以来修改的记录
            
            # 简化实现：导出所有数据（实际应用中应该实现真正的增量逻辑）
            self._export_database_data(db_backup_file)
            
            return db_backup_file if db_backup_file.exists() else None
            
        except Exception as e:
            logger.error(f"数据库增量备份失败: {e}")
            return None
    
    def _backup_files_incremental(self, backup_dir: Path, since_time: datetime) -> Optional[Path]:
        """增量备份文件"""
        try:
            files_backup_file = backup_dir / 'files_incremental.zip'
            
            upload_dir = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else 'uploads')
            if upload_dir.exists():
                with zipfile.ZipFile(files_backup_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in upload_dir.rglob('*'):
                        if file_path.is_file():
                            # 只备份修改时间晚于since_time的文件
                            if datetime.fromtimestamp(file_path.stat().st_mtime) > since_time:
                                arcname = file_path.relative_to(upload_dir.parent)
                                zip_file.write(file_path, arcname)
            
            return files_backup_file if files_backup_file.exists() else None
            
        except Exception as e:
            logger.error(f"文件增量备份失败: {e}")
            return None
    
    def _restore_database(self, restore_dir: Path) -> None:
        """恢复数据库"""
        db_backup_file = restore_dir / 'database_backup.sql'
        if not db_backup_file.exists():
            raise ValidationException("数据库备份文件不存在")
        
        # 这里应该实现数据库恢复逻辑
        # 注意：实际恢复前应该备份当前数据库
        logger.warning("数据库恢复功能需要根据具体数据库类型实现")
    
    def _restore_files(self, restore_dir: Path) -> None:
        """恢复文件"""
        files_backup_file = restore_dir / 'files_backup.zip'
        if not files_backup_file.exists():
            raise ValidationException("文件备份不存在")
        
        upload_dir = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else 'uploads')
        
        with zipfile.ZipFile(files_backup_file, 'r') as zip_file:
            zip_file.extractall(upload_dir.parent)
    
    def _restore_config(self, restore_dir: Path) -> None:
        """恢复配置"""
        config_backup_file = restore_dir / 'config_backup.zip'
        if not config_backup_file.exists():
            raise ValidationException("配置备份不存在")
        
        project_root = Path.cwd()
        
        with zipfile.ZipFile(config_backup_file, 'r') as zip_file:
            zip_file.extractall(project_root)
    
    def _create_archive(self, source_dir: Path, archive_path: Path) -> None:
        """创建压缩包"""
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zip_file.write(file_path, arcname)
    
    def _extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        """解压压缩包"""
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            zip_file.extractall(extract_dir)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'timestamp': datetime.now(),
            'python_version': os.sys.version,
            'platform': os.name,
            'cwd': str(Path.cwd())
        }
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """获取数据库架构信息"""
        try:
            db = SessionLocal()
            # 获取表信息
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            db.close()
            
            return {
                'tables': tables,
                'schema_version': '1.0'
            }
        except Exception as e:
            logger.warning(f"获取数据库架构失败: {e}")
            return {}
    
    def _export_database_data(self, output_file: Path) -> None:
        """导出数据库数据"""
        try:
            db = SessionLocal()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # 获取所有表
                result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [row[0] for row in result.fetchall()]
                
                for table in tables:
                    if table.startswith('sqlite_'):
                        continue
                    
                    f.write(f"-- Table: {table}\n")
                    
                    # 导出表数据
                    result = db.execute(text(f"SELECT * FROM {table}"))
                    rows = result.fetchall()
                    
                    if rows:
                        columns = result.keys()
                        f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
                        
                        for i, row in enumerate(rows):
                            values = [f"'{str(val).replace("'", "''")}" if val is not None else 'NULL' for val in row]
                            f.write(f"({', '.join(values)})")
                            if i < len(rows) - 1:
                                f.write(",\n")
                            else:
                                f.write(";\n\n")
            
            db.close()
            
        except Exception as e:
            logger.error(f"导出数据库数据失败: {e}")
            raise
    
    def _save_backup_record(self, backup_info: Dict[str, Any]) -> None:
        """保存备份记录"""
        try:
            # 这里应该保存到数据库，简化为保存到JSON文件
            records_file = self.backup_dir / 'backup_records.json'
            
            records = []
            if records_file.exists():
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            records.append(backup_info)
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存备份记录失败: {e}")
    
    def _save_restore_record(self, restore_info: Dict[str, Any]) -> None:
        """保存恢复记录"""
        try:
            records_file = self.backup_dir / 'restore_records.json'
            
            records = []
            if records_file.exists():
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            records.append(restore_info)
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存恢复记录失败: {e}")
    
    def _get_backup_record(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """获取备份记录"""
        try:
            records_file = self.backup_dir / 'backup_records.json'
            if not records_file.exists():
                return None
            
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            for record in records:
                if record.get('backup_id') == backup_id:
                    return record
            
            return None
            
        except Exception as e:
            logger.error(f"获取备份记录失败: {e}")
            return None
    
    def _get_backup_records(self, backup_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取备份记录列表"""
        try:
            records_file = self.backup_dir / 'backup_records.json'
            if not records_file.exists():
                return []
            
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            # 过滤备份类型
            if backup_type:
                records = [r for r in records if r.get('backup_type') == backup_type]
            
            # 按创建时间排序
            records.sort(key=lambda x: x.get('created_time', ''), reverse=True)
            
            return records[:limit]
            
        except Exception as e:
            logger.error(f"获取备份记录列表失败: {e}")
            return []
    
    def _get_expired_backups(self, backup_type: str, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """获取过期备份"""
        try:
            records = self._get_backup_records(backup_type)
            expired = []
            
            for record in records:
                created_time = record.get('created_time')
                if isinstance(created_time, str):
                    created_time = datetime.fromisoformat(created_time)
                
                if created_time and created_time < cutoff_date:
                    expired.append(record)
            
            return expired
            
        except Exception as e:
            logger.error(f"获取过期备份失败: {e}")
            return []
    
    def _delete_backup_record(self, backup_id: str) -> None:
        """删除备份记录"""
        try:
            records_file = self.backup_dir / 'backup_records.json'
            if not records_file.exists():
                return
            
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            records = [r for r in records if r.get('backup_id') != backup_id]
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"删除备份记录失败: {e}")
    
    def _deep_content_validation(self, backup_file: Path, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度内容验证
        
        Args:
            backup_file: 备份文件路径
            backup_info: 备份信息
            
        Returns:
            Dict: 验证结果
        """
        try:
            result = {'valid': True, 'errors': [], 'details': {}}
            
            with zipfile.ZipFile(backup_file, 'r') as zip_file:
                file_list = zip_file.namelist()
                result['details']['file_count'] = len(file_list)
                
                # 检查必要文件是否存在
                required_files = ['database/', 'files/', 'config/']
                missing_files = []
                
                for req_file in required_files:
                    if not any(f.startswith(req_file) for f in file_list):
                        missing_files.append(req_file)
                
                if missing_files:
                    result['valid'] = False
                    result['errors'].append(f'缺少必要文件/目录: {", ".join(missing_files)}')
                
                # 检查数据库文件完整性
                db_files = [f for f in file_list if f.startswith('database/') and f.endswith('.sql')]
                if db_files:
                    for db_file in db_files:
                        try:
                            content = zip_file.read(db_file).decode('utf-8')
                            if not content.strip():
                                result['valid'] = False
                                result['errors'].append(f'数据库文件为空: {db_file}')
                        except Exception as e:
                            result['valid'] = False
                            result['errors'].append(f'无法读取数据库文件 {db_file}: {e}')
                
                result['details']['database_files'] = len(db_files)
                result['details']['config_files'] = len([f for f in file_list if f.startswith('config/')])
                result['details']['uploaded_files'] = len([f for f in file_list if f.startswith('files/')])
            
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'深度验证失败: {e}'],
                'details': {}
            }
    
    def _get_storage_usage(self) -> Dict[str, Any]:
        """
        获取存储使用情况
        
        Returns:
            Dict: 存储使用情况
        """
        try:
            total_size = 0
            file_count = 0
            
            for backup_file in self.backup_dir.glob('*.zip'):
                if backup_file.is_file():
                    total_size += backup_file.stat().st_size
                    file_count += 1
            
            # 获取磁盘空间信息
            import shutil
            disk_usage = shutil.disk_usage(self.backup_dir)
            
            return {
                'total_backup_size': total_size,
                'backup_file_count': file_count,
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'backup_percentage': (total_size / disk_usage.total) * 100 if disk_usage.total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {e}")
            return {'error': str(e)}
    
    def _update_backup_record(self, backup_info: Dict[str, Any]) -> bool:
        """
        更新备份记录
        
        Args:
            backup_info: 备份信息
            
        Returns:
            bool: 是否更新成功
        """
        try:
            records_file = self.backup_dir / 'backup_records.json'
            records = []
            
            if records_file.exists():
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            backup_id = backup_info.get('backup_id')
            if backup_id:
                backup_info['updated_time'] = datetime.now().isoformat()
                
                # 查找并更新现有记录
                updated = False
                for i, record in enumerate(records):
                    if record.get('backup_id') == backup_id:
                        records[i] = backup_info
                        updated = True
                        break
                
                # 如果没有找到，添加新记录
                if not updated:
                    records.append(backup_info)
                
                with open(records_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, default=str, ensure_ascii=False)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新备份记录失败: {e}")
            return False
    
    def _get_restore_records_for_backup(self, backup_id: str) -> List[Dict[str, Any]]:
        """
        获取指定备份的恢复记录
        
        Args:
            backup_id: 备份ID
            
        Returns:
            List: 恢复记录列表
        """
        try:
            restore_file = self.backup_dir / 'restore_records.json'
            if not restore_file.exists():
                return []
            
            with open(restore_file, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
            
            return [record for record in all_records if record.get('backup_id') == backup_id]
            
        except Exception as e:
            logger.error(f"获取恢复记录失败: {e}")
            return []
    
    def _get_verification_records(self, backup_id: str) -> List[Dict[str, Any]]:
        """
        获取验证记录
        
        Args:
            backup_id: 备份ID
            
        Returns:
            List: 验证记录列表
        """
        try:
            verification_file = self.backup_dir / 'verification_records.json'
            if not verification_file.exists():
                return []
            
            with open(verification_file, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
            
            return [record for record in all_records if record.get('backup_id') == backup_id]
            
        except Exception as e:
            logger.error(f"获取验证记录失败: {e}")
            return []
    
    def _get_operation_records(self, backup_id: str) -> List[Dict[str, Any]]:
        """
        获取操作记录
        
        Args:
            backup_id: 备份ID
            
        Returns:
            List: 操作记录列表
        """
        try:
            operation_file = self.backup_dir / 'operation_records.json'
            if not operation_file.exists():
                return []
            
            with open(operation_file, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
            
            return [record for record in all_records if record.get('backup_id') == backup_id]
            
        except Exception as e:
            logger.error(f"获取操作记录失败: {e}")
            return []
    
    def _build_backup_timeline(self, backup_info: Dict[str, Any], restore_records: List[Dict[str, Any]], 
                              verification_records: List[Dict[str, Any]], operation_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        构建备份时间线
        
        Args:
            backup_info: 备份信息
            restore_records: 恢复记录
            verification_records: 验证记录
            operation_records: 操作记录
            
        Returns:
            List: 时间线事件列表
        """
        timeline = []
        
        # 添加备份创建事件
        if backup_info.get('created_time'):
            timeline.append({
                'time': backup_info['created_time'],
                'type': 'backup_created',
                'description': f"备份创建: {backup_info.get('backup_name', '')}",
                'details': backup_info
            })
        
        # 添加恢复事件
        for record in restore_records:
            if record.get('restore_time'):
                timeline.append({
                    'time': record['restore_time'],
                    'type': 'backup_restored',
                    'description': f"备份恢复: {record.get('status', '')}",
                    'details': record
                })
        
        # 添加验证事件
        for record in verification_records:
            if record.get('verified_time'):
                timeline.append({
                    'time': record['verified_time'],
                    'type': 'backup_verified',
                    'description': f"备份验证: {record.get('status', '')}",
                    'details': record
                })
        
        # 添加操作事件
        for record in operation_records:
            if record.get('operation_time'):
                timeline.append({
                    'time': record['operation_time'],
                    'type': 'backup_operation',
                    'description': f"备份操作: {record.get('operation_type', '')}",
                    'details': record
                })
        
        # 按时间排序
        timeline.sort(key=lambda x: x['time'], reverse=True)
        
        return timeline
    
    def _optimize_backup_compression(self, backup_file: Path) -> Optional[Path]:
        """
        优化备份压缩
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            Optional[Path]: 优化后的文件路径
        """
        try:
            optimized_file = backup_file.parent / f"{backup_file.stem}_optimized.zip"
            
            with zipfile.ZipFile(backup_file, 'r') as source_zip:
                with zipfile.ZipFile(optimized_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as target_zip:
                    for file_info in source_zip.infolist():
                        data = source_zip.read(file_info.filename)
                        target_zip.writestr(file_info, data)
            
            # 检查是否真的优化了
            original_size = backup_file.stat().st_size
            optimized_size = optimized_file.stat().st_size
            
            if optimized_size < original_size:
                return optimized_file
            else:
                # 如果没有优化，删除临时文件
                optimized_file.unlink()
                return None
                
        except Exception as e:
            logger.error(f"优化备份压缩失败: {e}")
            return None
    
    async def get_backups_before_date(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """获取指定日期前的备份"""
        try:
            backups = []
            
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backup_time = datetime.fromisoformat(metadata.get('timestamp', ''))
                        if backup_time < cutoff_date:
                            backups.append({
                                'backup_id': backup_dir.name,
                                'timestamp': metadata.get('timestamp'),
                                'type': metadata.get('type'),
                                'size': metadata.get('size', 0)
                            })
            
            logger.info(f"找到 {len(backups)} 个指定日期前的备份")
            return backups
            
        except Exception as e:
            logger.error(f"获取指定日期前的备份失败: {str(e)}")
            return []
    
    async def get_backups_since_date(self, since_date: datetime) -> List[Dict[str, Any]]:
        """获取指定日期后的备份"""
        try:
            backups = []
            
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backup_time = datetime.fromisoformat(metadata.get('timestamp', ''))
                        if backup_time >= since_date:
                            backups.append({
                                'backup_id': backup_dir.name,
                                'timestamp': metadata.get('timestamp'),
                                'type': metadata.get('type'),
                                'status': metadata.get('status', 'unknown'),
                                'size': metadata.get('size', 0)
                            })
            
            logger.info(f"找到 {len(backups)} 个指定日期后的备份")
            return backups
            
        except Exception as e:
            logger.error(f"获取指定日期后的备份失败: {str(e)}")
            return []
    
    async def archive_backup(self, backup_id: str) -> Dict[str, Any]:
        """归档备份"""
        try:
            backup_dir = self.backup_dir / backup_id
            if not backup_dir.exists():
                raise FileNotFoundError(f"备份目录不存在: {backup_id}")
            
            # 创建归档目录
            archive_dir = self.backup_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # 压缩备份到归档目录
            archive_file = archive_dir / f"{backup_id}.tar.gz"
            
            import tarfile
            with tarfile.open(archive_file, 'w:gz') as tar:
                tar.add(backup_dir, arcname=backup_id)
            
            # 更新元数据
            metadata_file = backup_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata['archived'] = True
                metadata['archive_file'] = str(archive_file)
                metadata['archive_time'] = datetime.now().isoformat()
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 删除原始备份目录
            import shutil
            shutil.rmtree(backup_dir)
            
            logger.info(f"备份归档成功: {backup_id} -> {archive_file}")
            return {
                "backup_id": backup_id,
                "archive_file": str(archive_file),
                "archive_size": archive_file.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"备份归档失败: {str(e)}")
            raise
    
    async def save_backup_report(self, report: Dict[str, Any]) -> str:
        """保存备份报告"""
        try:
            reports_dir = self.backup_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            report_date = datetime.now().strftime("%Y%m%d")
            report_file = reports_dir / f"backup_report_{report_date}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"备份报告保存成功: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"保存备份报告失败: {str(e)}")
            raise


# 全局备份服务实例
backup_service = BackupService()


# 导出主要接口
__all__ = [
    'BackupService',
    'backup_service'
]