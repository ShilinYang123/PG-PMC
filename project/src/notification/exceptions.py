"""通知系统异常类定义

定义了通知系统中可能出现的各种异常类型。
"""


class NotificationError(Exception):
    """通知系统基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ChannelError(NotificationError):
    """通知渠道异常"""
    
    def __init__(self, channel_name: str, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code, details)
        self.channel_name = channel_name
    
    def __str__(self):
        return f"Channel '{self.channel_name}': {super().__str__()}"


class ChannelUnavailableError(ChannelError):
    """通知渠道不可用异常"""
    pass


class ChannelConfigError(ChannelError):
    """通知渠道配置错误异常"""
    pass


class MessageError(NotificationError):
    """消息相关异常"""
    
    def __init__(self, message_id: str, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code, details)
        self.message_id = message_id
    
    def __str__(self):
        return f"Message '{self.message_id}': {super().__str__()}"


class MessageValidationError(MessageError):
    """消息验证异常"""
    pass


class MessageSendError(MessageError):
    """消息发送异常"""
    pass


class RetryError(NotificationError):
    """重试相关异常"""
    pass


class RetryExhaustedError(RetryError):
    """重试次数耗尽异常"""
    
    def __init__(self, message_id: str, retry_count: int, last_error: str = None):
        message = f"Retry exhausted for message '{message_id}' after {retry_count} attempts"
        if last_error:
            message += f". Last error: {last_error}"
        super().__init__(message)
        self.message_id = message_id
        self.retry_count = retry_count
        self.last_error = last_error


class QueueError(NotificationError):
    """消息队列异常"""
    pass


class QueueFullError(QueueError):
    """消息队列已满异常"""
    pass


class DatabaseError(NotificationError):
    """数据库相关异常"""
    pass


class ConfigurationError(NotificationError):
    """配置相关异常"""
    pass


class AuthenticationError(NotificationError):
    """认证相关异常"""
    pass


class RateLimitError(NotificationError):
    """频率限制异常"""
    
    def __init__(self, channel_name: str, limit: int, window: int, retry_after: int = None):
        message = f"Rate limit exceeded for channel '{channel_name}': {limit} requests per {window} seconds"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)
        self.channel_name = channel_name
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


class TemplateError(NotificationError):
    """模板相关异常"""
    
    def __init__(self, template_name: str, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code, details)
        self.template_name = template_name
    
    def __str__(self):
        return f"Template '{self.template_name}': {super().__str__()}"


class TemplateNotFoundError(TemplateError):
    """模板未找到异常"""
    pass


class TemplateRenderError(TemplateError):
    """模板渲染异常"""
    pass


class WebhookError(NotificationError):
    """Webhook相关异常"""
    
    def __init__(self, message: str, status_code: int = None, error_code: str = None, details: dict = None):
        super().__init__(message, error_code, details)
        self.status_code = status_code
    
    def __str__(self):
        if self.status_code:
            return f"[HTTP {self.status_code}] {super().__str__()}"
        return super().__str__()