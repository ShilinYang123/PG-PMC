"""通知系统工具函数

提供各种实用工具函数，包括消息格式化、时间处理、加密解密等。
"""

import re
import json
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from urllib.parse import quote, urlencode
import logging

logger = logging.getLogger(__name__)


def format_message_content(content: str, message_type: str = "text") -> str:
    """格式化消息内容
    
    Args:
        content: 原始内容
        message_type: 消息类型
        
    Returns:
        str: 格式化后的内容
    """
    if message_type == "markdown":
        # 确保Markdown格式正确
        content = content.strip()
        if not content.startswith('#') and not content.startswith('**'):
            # 如果不是标题或粗体开头，添加换行
            content = content.replace('\n', '\n\n')
    
    elif message_type == "text":
        # 文本消息，移除多余的空白
        content = re.sub(r'\n\s*\n', '\n', content.strip())
    
    return content


def validate_wechat_webhook_url(url: str) -> bool:
    """验证企业微信Webhook URL
    
    Args:
        url: Webhook URL
        
    Returns:
        bool: 是否有效
    """
    pattern = r'https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[a-zA-Z0-9-_]+'
    return bool(re.match(pattern, url))


def generate_wechat_signature(timestamp: str, nonce: str, secret: str, body: str) -> str:
    """生成企业微信签名
    
    Args:
        timestamp: 时间戳
        nonce: 随机数
        secret: 密钥
        body: 请求体
        
    Returns:
        str: 签名
    """
    string_to_sign = f"{timestamp}\n{nonce}\n{body}\n"
    signature = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')


def create_wechat_bot_url(webhook_url: str, timestamp: str, nonce: str, signature: str) -> str:
    """创建企业微信机器人请求URL
    
    Args:
        webhook_url: Webhook URL
        timestamp: 时间戳
        nonce: 随机数
        signature: 签名
        
    Returns:
        str: 完整的请求URL
    """
    params = {
        'timestamp': timestamp,
        'nonce': nonce,
        'signature': signature
    }
    
    separator = '&' if '?' in webhook_url else '?'
    return f"{webhook_url}{separator}{urlencode(params)}"


def sanitize_message_content(content: str, max_length: int = 4096) -> str:
    """清理和截断消息内容
    
    Args:
        content: 原始内容
        max_length: 最大长度
        
    Returns:
        str: 清理后的内容
    """
    # 移除危险字符
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # 截断过长内容
    if len(content) > max_length:
        content = content[:max_length-3] + '...'
    
    return content


def extract_mentions(content: str) -> List[str]:
    """提取消息中的@提及
    
    Args:
        content: 消息内容
        
    Returns:
        List[str]: 提及的用户列表
    """
    pattern = r'@([a-zA-Z0-9_\u4e00-\u9fa5]+)'
    return re.findall(pattern, content)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化的大小
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def parse_duration(duration_str: str) -> int:
    """解析时间间隔字符串
    
    Args:
        duration_str: 时间间隔字符串，如 "5m", "1h", "30s"
        
    Returns:
        int: 秒数
    """
    pattern = r'^(\d+)([smhd])$'
    match = re.match(pattern, duration_str.lower())
    
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")
    
    value, unit = match.groups()
    value = int(value)
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    return value * multipliers[unit]


def format_duration(seconds: int) -> str:
    """格式化时间间隔
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间间隔
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        return f"{seconds // 3600}h"
    else:
        return f"{seconds // 86400}d"


def generate_message_id() -> str:
    """生成消息ID
    
    Returns:
        str: 消息ID
    """
    timestamp = str(int(time.time() * 1000))
    random_part = hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
    return f"msg_{timestamp}_{random_part}"


def calculate_retry_delay(attempt: int, base_delay: int = 1, max_delay: int = 300) -> int:
    """计算重试延迟（指数退避）
    
    Args:
        attempt: 重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        
    Returns:
        int: 延迟秒数
    """
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


def is_business_hours(start_hour: int = 9, end_hour: int = 18) -> bool:
    """检查是否在工作时间
    
    Args:
        start_hour: 开始小时
        end_hour: 结束小时
        
    Returns:
        bool: 是否在工作时间
    """
    now = datetime.now()
    current_hour = now.hour
    
    # 检查是否是工作日（周一到周五）
    if now.weekday() >= 5:  # 周六、周日
        return False
    
    return start_hour <= current_hour < end_hour


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """遮蔽敏感数据
    
    Args:
        data: 原始数据
        mask_char: 遮蔽字符
        visible_chars: 可见字符数
        
    Returns:
        str: 遮蔽后的数据
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)
    return visible_part + masked_part


def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """验证JSON数据结构
    
    Args:
        data: 数据字典
        required_fields: 必需字段列表
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    for field in required_fields:
        if '.' in field:
            # 嵌套字段
            keys = field.split('.')
            current = data
            
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    errors.append(f"Missing required field: {field}")
                    break
                current = current[key]
        else:
            # 顶级字段
            if field not in data:
                errors.append(f"Missing required field: {field}")
    
    return errors


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """转义Markdown特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 转义后的文本
    """
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def unescape_markdown(text: str) -> str:
    """反转义Markdown特殊字符
    
    Args:
        text: 转义后的文本
        
    Returns:
        str: 原始文本
    """
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    
    for char in special_chars:
        text = text.replace(f'\\{char}', char)
    
    return text


def create_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """创建Markdown表格
    
    Args:
        headers: 表头
        rows: 数据行
        
    Returns:
        str: Markdown表格
    """
    if not headers or not rows:
        return ""
    
    # 计算每列的最大宽度
    col_widths = [len(header) for header in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 构建表格
    lines = []
    
    # 表头
    header_line = "| " + " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers)) + " |"
    lines.append(header_line)
    
    # 分隔线
    separator_line = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"
    lines.append(separator_line)
    
    # 数据行
    for row in rows:
        row_line = "| " + " | ".join(str(row[i]).ljust(col_widths[i]) if i < len(row) else " " * col_widths[i] for i in range(len(headers))) + " |"
        lines.append(row_line)
    
    return "\n".join(lines)


def parse_template_variables(template: str) -> List[str]:
    """解析模板中的变量
    
    Args:
        template: 模板字符串
        
    Returns:
        List[str]: 变量列表
    """
    pattern = r'\{([^}]+)\}'
    return list(set(re.findall(pattern, template)))


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """渲染模板
    
    Args:
        template: 模板字符串
        variables: 变量字典
        
    Returns:
        str: 渲染后的字符串
    """
    result = template
    
    for key, value in variables.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    
    return result


def get_current_timestamp() -> str:
    """获取当前时间戳字符串
    
    Returns:
        str: 时间戳字符串
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(timestamp_str: str) -> datetime:
    """解析时间戳字符串
    
    Args:
        timestamp_str: 时间戳字符串
        
    Returns:
        datetime: 时间对象
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def calculate_time_ago(timestamp: datetime) -> str:
    """计算时间差描述
    
    Args:
        timestamp: 时间戳
        
    Returns:
        str: 时间差描述
    """
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"


def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """创建进度条
    
    Args:
        current: 当前值
        total: 总值
        width: 进度条宽度
        
    Returns:
        str: 进度条字符串
    """
    if total == 0:
        return "[" + " " * width + "] 0%"
    
    percentage = min(100, int((current / total) * 100))
    filled = int((current / total) * width)
    
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage}%"


def compress_json(data: Dict[str, Any]) -> str:
    """压缩JSON数据
    
    Args:
        data: 数据字典
        
    Returns:
        str: 压缩后的JSON字符串
    """
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全解析JSON
    
    Args:
        json_str: JSON字符串
        default: 默认值
        
    Returns:
        Any: 解析结果
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def normalize_phone_number(phone: str) -> str:
    """标准化手机号码
    
    Args:
        phone: 原始手机号
        
    Returns:
        str: 标准化后的手机号
    """
    # 移除所有非数字字符
    phone = re.sub(r'\D', '', phone)
    
    # 处理中国手机号
    if phone.startswith('86') and len(phone) == 13:
        phone = phone[2:]
    elif phone.startswith('+86') and len(phone) == 14:
        phone = phone[3:]
    
    return phone


def validate_email(email: str) -> bool:
    """验证邮箱地址
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_random_string(length: int = 8) -> str:
    """生成随机字符串
    
    Args:
        length: 字符串长度
        
    Returns:
        str: 随机字符串
    """
    import string
    import random
    
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def rate_limit_key(identifier: str, window: str = "1h") -> str:
    """生成限流键
    
    Args:
        identifier: 标识符
        window: 时间窗口
        
    Returns:
        str: 限流键
    """
    timestamp = int(time.time())
    window_seconds = parse_duration(window)
    window_start = (timestamp // window_seconds) * window_seconds
    
    return f"rate_limit:{identifier}:{window_start}"


class MessageFormatter:
    """消息格式化器"""
    
    @staticmethod
    def format_alert(level: str, message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """格式化告警消息
        
        Args:
            level: 告警级别
            message: 告警消息
            details: 详细信息
            
        Returns:
            str: 格式化后的消息
        """
        level_emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = level_emojis.get(level.lower(), "📢")
        formatted = f"{emoji} **{level.upper()}**\n\n{message}"
        
        if details:
            formatted += "\n\n**详细信息：**\n"
            for key, value in details.items():
                formatted += f"- {key}: {value}\n"
        
        formatted += f"\n**时间：** {get_current_timestamp()}"
        
        return formatted
    
    @staticmethod
    def format_task_status(task_name: str, status: str, progress: Optional[int] = None, 
                          details: Optional[str] = None) -> str:
        """格式化任务状态消息
        
        Args:
            task_name: 任务名称
            status: 任务状态
            progress: 进度百分比
            details: 详细信息
            
        Returns:
            str: 格式化后的消息
        """
        status_emojis = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️",
            "cancelled": "🚫"
        }
        
        emoji = status_emojis.get(status.lower(), "📋")
        formatted = f"{emoji} **任务状态更新**\n\n"
        formatted += f"**任务：** {task_name}\n"
        formatted += f"**状态：** {status}\n"
        
        if progress is not None:
            progress_bar = create_progress_bar(progress, 100, 15)
            formatted += f"**进度：** {progress_bar}\n"
        
        if details:
            formatted += f"**详情：** {details}\n"
        
        formatted += f"**更新时间：** {get_current_timestamp()}"
        
        return formatted
    
    @staticmethod
    def format_data_report(title: str, data: Dict[str, Any], 
                          chart_url: Optional[str] = None) -> str:
        """格式化数据报告消息
        
        Args:
            title: 报告标题
            data: 数据字典
            chart_url: 图表URL
            
        Returns:
            str: 格式化后的消息
        """
        formatted = f"📊 **{title}**\n\n"
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    value = f"{value:.2f}"
                formatted += f"**{key}：** {value}\n"
            else:
                formatted += f"**{key}：** {value}\n"
        
        if chart_url:
            formatted += f"\n[查看图表]({chart_url})"
        
        formatted += f"\n\n**生成时间：** {get_current_timestamp()}"
        
        return formatted