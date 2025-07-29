"""邮件服务

实现邮件发送功能，支持：
- SMTP邮件发送
- HTML邮件模板
- 附件支持
- 批量邮件发送
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Template
from loguru import logger
import os


@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    sender_name: str = "PMC生产管理系统"
    sender_email: Optional[str] = None
    
    def __post_init__(self):
        if not self.sender_email:
            self.sender_email = self.username


@dataclass
class EmailTemplate:
    """邮件模板"""
    template_id: str
    template_name: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    required_params: List[str] = None
    
    def __post_init__(self):
        if self.required_params is None:
            self.required_params = []


@dataclass
class EmailMessage:
    """邮件消息"""
    to_emails: List[str]
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    attachments: List[str] = None
    cc_emails: List[str] = None
    bcc_emails: List[str] = None
    reply_to: Optional[str] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.cc_emails is None:
            self.cc_emails = []
        if self.bcc_emails is None:
            self.bcc_emails = []


class EmailService:
    """邮件服务"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.templates = self._load_default_templates()
        
    def _load_default_templates(self) -> Dict[str, EmailTemplate]:
        """加载默认邮件模板"""
        templates = {
            "order_notification": EmailTemplate(
                template_id="order_notification",
                template_name="订单通知",
                subject_template="订单通知 - {{order_no}}",
                html_template="""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .highlight { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>PMC生产管理系统</h1>
                        <h2>订单通知</h2>
                    </div>
                    <div class="content">
                        <p>尊敬的用户，</p>
                        <p>您的订单信息如下：</p>
                        <div class="highlight">
                            <p><strong>订单号：</strong>{{order_no}}</p>
                            <p><strong>客户：</strong>{{customer_name}}</p>
                            <p><strong>产品：</strong>{{product_name}}</p>
                            <p><strong>数量：</strong>{{quantity}}</p>
                            <p><strong>交期：</strong>{{delivery_date}}</p>
                            <p><strong>状态：</strong>{{status}}</p>
                        </div>
                        <p>如有疑问，请及时联系我们。</p>
                    </div>
                    <div class="footer">
                        <p>此邮件由PMC生产管理系统自动发送，请勿回复。</p>
                        <p>发送时间：{{send_time}}</p>
                    </div>
                </body>
                </html>
                """,
                text_template="""
                PMC生产管理系统 - 订单通知
                
                尊敬的用户，
                
                您的订单信息如下：
                订单号：{{order_no}}
                客户：{{customer_name}}
                产品：{{product_name}}
                数量：{{quantity}}
                交期：{{delivery_date}}
                状态：{{status}}
                
                如有疑问，请及时联系我们。
                
                此邮件由PMC生产管理系统自动发送，请勿回复。
                发送时间：{{send_time}}
                """,
                required_params=["order_no", "customer_name", "product_name", "quantity", "delivery_date", "status"]
            ),
            
            "production_report": EmailTemplate(
                template_id="production_report",
                template_name="生产报告",
                subject_template="生产日报 - {{report_date}}",
                html_template="""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #2196F3; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                        .stat-item { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }
                        .stat-number { font-size: 24px; font-weight: bold; color: #2196F3; }
                        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>PMC生产管理系统</h1>
                        <h2>生产日报</h2>
                    </div>
                    <div class="content">
                        <h3>{{report_date}} 生产统计</h3>
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-number">{{total_orders}}</div>
                                <div>总订单数</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">{{completed_orders}}</div>
                                <div>完成订单</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">{{production_efficiency}}%</div>
                                <div>生产效率</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-number">{{quality_rate}}%</div>
                                <div>合格率</div>
                            </div>
                        </div>
                        
                        <h4>详细数据</h4>
                        <table>
                            <tr>
                                <th>指标</th>
                                <th>数值</th>
                                <th>备注</th>
                            </tr>
                            {% for item in detail_data %}
                            <tr>
                                <td>{{item.metric}}</td>
                                <td>{{item.value}}</td>
                                <td>{{item.note}}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                    <div class="footer">
                        <p>此邮件由PMC生产管理系统自动发送，请勿回复。</p>
                        <p>发送时间：{{send_time}}</p>
                    </div>
                </body>
                </html>
                """,
                required_params=["report_date", "total_orders", "completed_orders", "production_efficiency", "quality_rate"]
            ),
            
            "alert_notification": EmailTemplate(
                template_id="alert_notification",
                template_name="异常告警",
                subject_template="【紧急】生产异常告警 - {{alert_type}}",
                html_template="""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .alert { background-color: #ffebee; border: 1px solid #f44336; padding: 15px; border-radius: 5px; margin: 15px 0; }
                        .urgent { color: #f44336; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>PMC生产管理系统</h1>
                        <h2 class="urgent">⚠️ 异常告警</h2>
                    </div>
                    <div class="content">
                        <div class="alert">
                            <h3>{{alert_type}}</h3>
                            <p><strong>发生时间：</strong>{{alert_time}}</p>
                            <p><strong>影响范围：</strong>{{affected_area}}</p>
                            <p><strong>详细描述：</strong></p>
                            <p>{{alert_description}}</p>
                            <p><strong>建议处理：</strong>{{suggested_action}}</p>
                        </div>
                        <p class="urgent">请立即处理此异常情况！</p>
                    </div>
                    <div class="footer">
                        <p>此邮件由PMC生产管理系统自动发送，请勿回复。</p>
                        <p>发送时间：{{send_time}}</p>
                    </div>
                </body>
                </html>
                """,
                required_params=["alert_type", "alert_time", "affected_area", "alert_description", "suggested_action"]
            )
        }
        return templates
    
    async def send_email(self, message: EmailMessage) -> bool:
        """发送邮件"""
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.config.sender_name, self.config.sender_email))
            msg['To'] = ', '.join(message.to_emails)
            msg['Subject'] = message.subject
            
            if message.cc_emails:
                msg['Cc'] = ', '.join(message.cc_emails)
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            
            # 添加邮件内容
            if message.text_content:
                text_part = MIMEText(message.text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if message.html_content:
                html_part = MIMEText(message.html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 添加附件
            for attachment_path in message.attachments:
                if os.path.exists(attachment_path):
                    self._add_attachment(msg, attachment_path)
            
            # 发送邮件
            return await self._send_smtp(msg, message.to_emails + message.cc_emails + message.bcc_emails)
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    async def send_template_email(self, to_emails: List[str], template_id: str, 
                                template_data: Dict[str, Any], 
                                attachments: List[str] = None,
                                cc_emails: List[str] = None) -> bool:
        """发送模板邮件"""
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return False
            
            # 添加发送时间
            template_data['send_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 渲染模板
            subject = Template(template.subject_template).render(**template_data)
            html_content = Template(template.html_template).render(**template_data)
            text_content = None
            if template.text_template:
                text_content = Template(template.text_template).render(**template_data)
            
            # 创建邮件消息
            message = EmailMessage(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=attachments or [],
                cc_emails=cc_emails or []
            )
            
            return await self.send_email(message)
            
        except Exception as e:
            logger.error(f"Template email sending failed: {e}")
            return False
    
    async def send_batch_emails(self, messages: List[EmailMessage]) -> List[bool]:
        """批量发送邮件"""
        results = []
        for message in messages:
            result = await self.send_email(message)
            results.append(result)
        return results
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """添加附件"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = Path(file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    async def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """通过SMTP发送邮件"""
        try:
            # 创建SMTP连接
            if self.config.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                if self.config.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # 登录
            server.login(self.config.username, self.config.password)
            
            # 发送邮件
            text = msg.as_string()
            server.sendmail(self.config.sender_email, recipients, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP sending failed: {e}")
            return False
    
    def add_template(self, template: EmailTemplate):
        """添加邮件模板"""
        self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """获取邮件模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[EmailTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
    
    async def send_order_notification(self, to_emails: List[str], order_data: Dict[str, Any]) -> bool:
        """发送订单通知"""
        return await self.send_template_email(
            to_emails=to_emails,
            template_id="order_notification",
            template_data=order_data
        )
    
    async def send_production_report(self, to_emails: List[str], report_data: Dict[str, Any]) -> bool:
        """发送生产报告"""
        return await self.send_template_email(
            to_emails=to_emails,
            template_id="production_report",
            template_data=report_data
        )
    
    async def send_alert_notification(self, to_emails: List[str], alert_data: Dict[str, Any]) -> bool:
        """发送异常告警"""
        return await self.send_template_email(
            to_emails=to_emails,
            template_id="alert_notification",
            template_data=alert_data
        )


# 默认邮件服务实例
email_config = EmailConfig(
    smtp_server="smtp.qq.com",  # 可以根据需要修改
    smtp_port=587,
    username="your_email@qq.com",
    password="your_password",
    use_tls=True,
    sender_name="PMC生产管理系统"
)

email_service = EmailService(email_config)