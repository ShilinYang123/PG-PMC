"""邮件集成模块

提供邮件发送的集成功能。
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging

from ..exceptions import ChannelError, AuthenticationError
from ..models import NotificationMessage

logger = logging.getLogger(__name__)


class EmailIntegration:
    """邮件集成类（预留实现）"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str,
                 use_tls: bool = True):
        """初始化邮件集成
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 用户名
            password: 密码
            use_tls: 是否使用TLS
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send_email(self, to_addresses: List[str], subject: str, 
                        content: str, content_type: str = 'plain',
                        attachments: Optional[List[str]] = None) -> bool:
        """发送邮件
        
        Args:
            to_addresses: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 ('plain' 或 'html')
            attachments: 附件文件路径列表
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {file_path.split("/")[-1]}'
                        )
                        msg.attach(part)
                    except Exception as e:
                        logger.warning(f"Failed to attach file {file_path}: {e}")
            
            # 发送邮件
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_addresses, msg.as_string())
            
            logger.info(f"Email sent successfully to {', '.join(to_addresses)}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """发送通知消息
        
        Args:
            message: 通知消息对象
            
        Returns:
            bool: 发送是否成功
        """
        to_addresses = message.recipients.get('emails', [])
        if not to_addresses:
            logger.warning("No email addresses specified in recipients")
            return False
        
        subject = message.title or "系统通知"
        content = message.content
        
        # 根据消息类型确定内容格式
        content_type = 'html' if message.message_type == 'html' else 'plain'
        
        return await self.send_email(
            to_addresses=to_addresses,
            subject=subject,
            content=content,
            content_type=content_type
        )
    
    def test_connection(self) -> bool:
        """测试邮件服务器连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
            
            logger.info("Email server connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email server connection test failed: {e}")
            return False