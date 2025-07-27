import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor
import traceback

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskResult:
    """任务结果"""
    total_records: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    download_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)

@dataclass
class Task:
    """任务信息"""
    task_id: str
    task_type: str
    status: TaskStatus
    progress: float
    message: str
    result: Optional[TaskResult]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": {
                "total_records": self.result.total_records if self.result else 0,
                "success_count": self.result.success_count if self.result else 0,
                "error_count": self.result.error_count if self.result else 0,
                "errors": self.result.errors if self.result else [],
                "download_url": self.result.download_url if self.result else None,
                "data": self.result.data if self.result else {}
            } if self.result else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata
        }

class TaskService:
    """任务管理服务"""
    
    def __init__(self, max_workers: int = 4, task_ttl_hours: int = 24):
        self.tasks: Dict[str, Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_ttl_hours = task_ttl_hours
        self._cleanup_task = None
        self._running = False
    
    async def start(self):
        """启动任务服务"""
        if self._running:
            return
        
        self._running = True
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_tasks())
        logger.info("任务服务已启动")
    
    async def stop(self):
        """停止任务服务"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        logger.info("任务服务已停止")
    
    def create_task(
        self,
        task_type: str,
        func: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            progress=0.0,
            message="任务已创建，等待执行",
            result=None,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=self.task_ttl_hours),
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        
        # 提交任务到线程池
        future = self.executor.submit(self._execute_task, task_id, func, *args, **kwargs)
        
        logger.info(f"任务 {task_id} 已创建，类型: {task_type}")
        return task_id
    
    def _execute_task(self, task_id: str, func: Callable, *args, **kwargs):
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return
        
        try:
            # 更新任务状态为处理中
            self._update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                0.0,
                "任务执行中..."
            )
            
            # 执行任务函数
            result = func(task_id, self._update_task_progress, *args, **kwargs)
            
            # 任务完成
            if isinstance(result, TaskResult):
                task_result = result
            else:
                task_result = TaskResult(data=result if result else {})
            
            self._update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                100.0,
                "任务执行完成",
                task_result
            )
            
            logger.info(f"任务 {task_id} 执行完成")
            
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            logger.error(f"任务 {task_id} 执行失败: {e}")
            logger.error(traceback.format_exc())
            
            # 创建错误结果
            error_result = TaskResult(
                error_count=1,
                errors=[{
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }]
            )
            
            self._update_task_status(
                task_id,
                TaskStatus.FAILED,
                0.0,
                error_msg,
                error_result
            )
    
    def _update_task_progress(self, task_id: str, progress: float, message: str = None):
        """更新任务进度"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.progress = max(0.0, min(100.0, progress))
        if message:
            task.message = message
        task.updated_at = datetime.utcnow()
        
        logger.debug(f"任务 {task_id} 进度更新: {progress}% - {message}")
    
    def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float = None,
        message: str = None,
        result: TaskResult = None
    ):
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = status
        if progress is not None:
            task.progress = max(0.0, min(100.0, progress))
        if message:
            task.message = message
        if result:
            task.result = result
        task.updated_at = datetime.utcnow()
        
        logger.info(f"任务 {task_id} 状态更新: {status.value} - {message}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        return task.to_dict()
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        self._update_task_status(
            task_id,
            TaskStatus.CANCELLED,
            task.progress,
            "任务已取消"
        )
        
        logger.info(f"任务 {task_id} 已取消")
        return True
    
    def list_tasks(
        self,
        task_type: str = None,
        status: TaskStatus = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        # 过滤条件
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 排序（按创建时间倒序）
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # 分页
        tasks = tasks[offset:offset + limit]
        
        return [task.to_dict() for task in tasks]
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"任务 {task_id} 已删除")
            return True
        return False
    
    def delete_tasks(self, task_ids: List[str]) -> int:
        """批量删除任务"""
        deleted_count = 0
        for task_id in task_ids:
            if self.delete_task(task_id):
                deleted_count += 1
        return deleted_count
    
    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        while self._running:
            try:
                now = datetime.utcnow()
                expired_task_ids = []
                
                for task_id, task in self.tasks.items():
                    if task.expires_at < now:
                        expired_task_ids.append(task_id)
                
                # 删除过期任务
                for task_id in expired_task_ids:
                    self.delete_task(task_id)
                
                if expired_task_ids:
                    logger.info(f"清理了 {len(expired_task_ids)} 个过期任务")
                
                # 每小时清理一次
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理过期任务时发生错误: {e}")
                await asyncio.sleep(300)  # 出错时5分钟后重试
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = len(self.tasks)
        status_counts = {}
        type_counts = {}
        
        for task in self.tasks.values():
            # 统计状态
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 统计类型
            task_type = task.task_type
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "active_workers": self.executor._threads if hasattr(self.executor, '_threads') else 0
        }

# 全局任务服务实例
task_service = TaskService()