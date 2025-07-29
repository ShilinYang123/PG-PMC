"""通知模板管理服务

管理通知模板，包括：
- 模板创建和编辑
- 模板变量替换
- 多语言支持
- 模板版本管理
"""

import json
import re
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from jinja2 import Template, Environment, BaseLoader
from loguru import logger


class TemplateType(Enum):
    """模板类型"""
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    SYSTEM = "system"


class TemplateCategory(Enum):
    """模板分类"""
    ORDER = "order"          # 订单相关
    PRODUCTION = "production" # 生产相关
    QUALITY = "quality"      # 质量相关
    DELIVERY = "delivery"    # 交期相关
    SYSTEM = "system"        # 系统相关
    ALERT = "alert"          # 告警相关


@dataclass
class TemplateVariable:
    """模板变量"""
    name: str
    type: str  # string, number, date, boolean
    description: str
    required: bool = True
    default_value: Optional[Any] = None
    format: Optional[str] = None  # 格式化规则


@dataclass
class NotificationTemplate:
    """通知模板"""
    id: str
    name: str
    type: TemplateType
    category: TemplateCategory
    title: str
    content: str
    variables: List[TemplateVariable]
    language: str = "zh-CN"
    version: str = "1.0.0"
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TemplateRenderResult:
    """模板渲染结果"""
    title: str
    content: str
    html_content: Optional[str] = None
    variables_used: List[str] = None
    render_time: float = 0.0
    
    def __post_init__(self):
        if self.variables_used is None:
            self.variables_used = []


class NotificationTemplateService:
    """通知模板管理服务"""
    
    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
        self.template_versions: Dict[str, List[NotificationTemplate]] = {}
        self.jinja_env = Environment(loader=BaseLoader())
        
        # 初始化默认模板
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = [
            # 订单相关模板
            NotificationTemplate(
                id="order_created",
                name="订单创建通知",
                type=TemplateType.EMAIL,
                category=TemplateCategory.ORDER,
                title="新订单创建通知 - 订单号：{{ order_number }}",
                content="""尊敬的 {{ customer_name }}，

您的订单已成功创建：
- 订单号：{{ order_number }}
- 产品名称：{{ product_name }}
- 数量：{{ quantity }}
- 交期：{{ delivery_date }}
- 总金额：{{ total_amount }}

我们将尽快安排生产，感谢您的信任！

{{ company_name }}
{{ contact_info }}""",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("customer_name", "string", "客户名称"),
                    TemplateVariable("product_name", "string", "产品名称"),
                    TemplateVariable("quantity", "number", "数量"),
                    TemplateVariable("delivery_date", "date", "交期", format="%Y-%m-%d"),
                    TemplateVariable("total_amount", "number", "总金额", format=",.2f"),
                    TemplateVariable("company_name", "string", "公司名称", default_value="PMC生产管理系统"),
                    TemplateVariable("contact_info", "string", "联系方式", default_value="客服电话：400-123-4567")
                ]
            ),
            
            NotificationTemplate(
                id="order_status_update",
                name="订单状态更新",
                type=TemplateType.SMS,
                category=TemplateCategory.ORDER,
                title="订单状态更新",
                content="【PMC系统】您的订单{{ order_number }}状态已更新为：{{ status }}。如有疑问请联系客服。",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("status", "string", "订单状态")
                ]
            ),
            
            # 生产相关模板
            NotificationTemplate(
                id="production_start",
                name="生产开始通知",
                type=TemplateType.WECHAT,
                category=TemplateCategory.PRODUCTION,
                title="生产开始通知",
                content="""订单 {{ order_number }} 已开始生产

产品：{{ product_name }}
数量：{{ quantity }}
预计完成：{{ estimated_completion }}
负责人：{{ responsible_person }}

请关注生产进度。""",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("product_name", "string", "产品名称"),
                    TemplateVariable("quantity", "number", "数量"),
                    TemplateVariable("estimated_completion", "date", "预计完成时间"),
                    TemplateVariable("responsible_person", "string", "负责人")
                ]
            ),
            
            NotificationTemplate(
                id="production_progress",
                name="生产进度更新",
                type=TemplateType.EMAIL,
                category=TemplateCategory.PRODUCTION,
                title="生产进度更新 - {{ order_number }}",
                content="""生产进度更新报告

订单号：{{ order_number }}
产品：{{ product_name }}
当前进度：{{ progress }}%
已完成数量：{{ completed_quantity }}/{{ total_quantity }}

{% if progress >= 100 %}
🎉 生产已完成！
{% elif progress >= 80 %}
⚡ 即将完成，请准备质检。
{% elif progress >= 50 %}
📈 生产进展顺利。
{% else %}
🔄 生产进行中。
{% endif %}

下次更新时间：{{ next_update }}""",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("product_name", "string", "产品名称"),
                    TemplateVariable("progress", "number", "进度百分比"),
                    TemplateVariable("completed_quantity", "number", "已完成数量"),
                    TemplateVariable("total_quantity", "number", "总数量"),
                    TemplateVariable("next_update", "date", "下次更新时间")
                ]
            ),
            
            # 质量相关模板
            NotificationTemplate(
                id="quality_alert",
                name="质量异常告警",
                type=TemplateType.SMS,
                category=TemplateCategory.QUALITY,
                title="质量异常告警",
                content="【紧急】订单{{ order_number }}发现质量问题：{{ issue_description }}。请立即处理！联系人：{{ contact_person }}",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("issue_description", "string", "问题描述"),
                    TemplateVariable("contact_person", "string", "联系人")
                ]
            ),
            
            # 交期相关模板
            NotificationTemplate(
                id="delivery_warning",
                name="交期预警",
                type=TemplateType.EMAIL,
                category=TemplateCategory.DELIVERY,
                title="⚠️ 交期预警 - {{ order_number }}",
                content="""交期预警通知

订单号：{{ order_number }}
客户：{{ customer_name }}
产品：{{ product_name }}
原定交期：{{ original_delivery_date }}
当前进度：{{ progress }}%
预计延期：{{ delay_days }}天

{% if delay_days > 7 %}
🚨 严重延期风险！
{% elif delay_days > 3 %}
⚠️ 中等延期风险
{% else %}
⚡ 轻微延期风险
{% endif %}

建议措施：
{{ suggested_actions }}

请及时采取行动确保按时交付。""",
                variables=[
                    TemplateVariable("order_number", "string", "订单号"),
                    TemplateVariable("customer_name", "string", "客户名称"),
                    TemplateVariable("product_name", "string", "产品名称"),
                    TemplateVariable("original_delivery_date", "date", "原定交期"),
                    TemplateVariable("progress", "number", "当前进度"),
                    TemplateVariable("delay_days", "number", "预计延期天数"),
                    TemplateVariable("suggested_actions", "string", "建议措施")
                ]
            ),
            
            # 系统相关模板
            NotificationTemplate(
                id="daily_report",
                name="每日生产报告",
                type=TemplateType.EMAIL,
                category=TemplateCategory.SYSTEM,
                title="每日生产报告 - {{ report_date }}",
                content="""每日生产报告

报告日期：{{ report_date }}

📊 生产统计：
- 新增订单：{{ new_orders }}个
- 生产中订单：{{ in_progress_orders }}个
- 完成订单：{{ completed_orders }}个
- 延期订单：{{ delayed_orders }}个

📈 产能利用率：{{ capacity_utilization }}%

🎯 关键指标：
- 按时交付率：{{ on_time_delivery_rate }}%
- 质量合格率：{{ quality_pass_rate }}%
- 设备利用率：{{ equipment_utilization }}%

{% if urgent_issues %}
🚨 紧急事项：
{% for issue in urgent_issues %}
- {{ issue }}
{% endfor %}
{% endif %}

详细报告请登录系统查看。""",
                variables=[
                    TemplateVariable("report_date", "date", "报告日期"),
                    TemplateVariable("new_orders", "number", "新增订单数"),
                    TemplateVariable("in_progress_orders", "number", "生产中订单数"),
                    TemplateVariable("completed_orders", "number", "完成订单数"),
                    TemplateVariable("delayed_orders", "number", "延期订单数"),
                    TemplateVariable("capacity_utilization", "number", "产能利用率"),
                    TemplateVariable("on_time_delivery_rate", "number", "按时交付率"),
                    TemplateVariable("quality_pass_rate", "number", "质量合格率"),
                    TemplateVariable("equipment_utilization", "number", "设备利用率"),
                    TemplateVariable("urgent_issues", "string", "紧急事项列表", required=False)
                ]
            )
        ]
        
        for template in default_templates:
            self.add_template(template)
    
    def add_template(self, template: NotificationTemplate) -> bool:
        """添加模板"""
        try:
            # 验证模板
            if not self._validate_template(template):
                return False
            
            # 保存模板
            self.templates[template.id] = template
            
            # 保存版本历史
            if template.id not in self.template_versions:
                self.template_versions[template.id] = []
            self.template_versions[template.id].append(template)
            
            logger.info(f"Added template {template.id} v{template.version}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding template: {e}")
            return False
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """更新模板"""
        try:
            if template_id not in self.templates:
                logger.warning(f"Template {template_id} not found")
                return False
            
            template = self.templates[template_id]
            
            # 创建新版本
            new_template = NotificationTemplate(
                id=template.id,
                name=updates.get("name", template.name),
                type=template.type,
                category=template.category,
                title=updates.get("title", template.title),
                content=updates.get("content", template.content),
                variables=updates.get("variables", template.variables),
                language=updates.get("language", template.language),
                version=self._increment_version(template.version),
                is_active=updates.get("is_active", template.is_active),
                metadata=updates.get("metadata", template.metadata)
            )
            
            # 验证新模板
            if not self._validate_template(new_template):
                return False
            
            # 停用旧版本
            template.is_active = False
            
            # 保存新版本
            self.templates[template_id] = new_template
            self.template_versions[template_id].append(new_template)
            
            logger.info(f"Updated template {template_id} to v{new_template.version}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return False
    
    def get_template(self, template_id: str, version: Optional[str] = None) -> Optional[NotificationTemplate]:
        """获取模板"""
        try:
            if template_id not in self.templates:
                return None
            
            if version is None:
                return self.templates[template_id]
            
            # 查找指定版本
            if template_id in self.template_versions:
                for template in self.template_versions[template_id]:
                    if template.version == version:
                        return template
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None
    
    def list_templates(self, type: Optional[TemplateType] = None,
                      category: Optional[TemplateCategory] = None,
                      active_only: bool = True) -> List[NotificationTemplate]:
        """列出模板"""
        try:
            templates = list(self.templates.values())
            
            if active_only:
                templates = [t for t in templates if t.is_active]
            
            if type:
                templates = [t for t in templates if t.type == type]
            
            if category:
                templates = [t for t in templates if t.category == category]
            
            return sorted(templates, key=lambda t: t.name)
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def render_template(self, template_id: str, variables: Dict[str, Any],
                       language: Optional[str] = None) -> Optional[TemplateRenderResult]:
        """渲染模板"""
        try:
            start_time = datetime.now()
            
            template = self.get_template(template_id)
            if not template:
                logger.warning(f"Template {template_id} not found")
                return None
            
            # 处理变量
            processed_vars = self._process_variables(template, variables)
            
            # 渲染标题
            title_template = self.jinja_env.from_string(template.title)
            rendered_title = title_template.render(**processed_vars)
            
            # 渲染内容
            content_template = self.jinja_env.from_string(template.content)
            rendered_content = content_template.render(**processed_vars)
            
            # 生成HTML内容（如果是邮件模板）
            html_content = None
            if template.type == TemplateType.EMAIL:
                html_content = self._convert_to_html(rendered_content)
            
            # 计算渲染时间
            render_time = (datetime.now() - start_time).total_seconds()
            
            # 提取使用的变量
            variables_used = self._extract_variables_used(template.title + template.content)
            
            return TemplateRenderResult(
                title=rendered_title,
                content=rendered_content,
                html_content=html_content,
                variables_used=variables_used,
                render_time=render_time
            )
            
        except Exception as e:
            logger.error(f"Error rendering template {template_id}: {e}")
            return None
    
    def validate_variables(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板变量"""
        try:
            template = self.get_template(template_id)
            if not template:
                return {"valid": False, "error": "Template not found"}
            
            errors = []
            warnings = []
            
            # 检查必需变量
            for var in template.variables:
                if var.required and var.name not in variables:
                    errors.append(f"Required variable '{var.name}' is missing")
                elif var.name in variables:
                    # 验证变量类型
                    value = variables[var.name]
                    if not self._validate_variable_type(value, var.type):
                        errors.append(f"Variable '{var.name}' has invalid type, expected {var.type}")
            
            # 检查多余变量
            template_var_names = {var.name for var in template.variables}
            for var_name in variables:
                if var_name not in template_var_names:
                    warnings.append(f"Unknown variable '{var_name}' will be ignored")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error validating variables: {e}")
            return {"valid": False, "error": str(e)}
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        try:
            if template_id not in self.templates:
                return False
            
            # 标记为非活跃而不是直接删除
            self.templates[template_id].is_active = False
            
            logger.info(f"Deactivated template {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    def clone_template(self, template_id: str, new_id: str, new_name: str) -> bool:
        """克隆模板"""
        try:
            template = self.get_template(template_id)
            if not template:
                return False
            
            new_template = NotificationTemplate(
                id=new_id,
                name=new_name,
                type=template.type,
                category=template.category,
                title=template.title,
                content=template.content,
                variables=template.variables.copy(),
                language=template.language,
                version="1.0.0",
                metadata=template.metadata.copy() if template.metadata else {}
            )
            
            return self.add_template(new_template)
            
        except Exception as e:
            logger.error(f"Error cloning template: {e}")
            return False
    
    def _validate_template(self, template: NotificationTemplate) -> bool:
        """验证模板"""
        try:
            # 检查基本字段
            if not template.id or not template.name or not template.title or not template.content:
                logger.error("Template missing required fields")
                return False
            
            # 验证Jinja2语法
            try:
                self.jinja_env.from_string(template.title)
                self.jinja_env.from_string(template.content)
            except Exception as e:
                logger.error(f"Template syntax error: {e}")
                return False
            
            # 验证变量定义
            template_vars = self._extract_variables_used(template.title + template.content)
            defined_vars = {var.name for var in template.variables}
            
            undefined_vars = template_vars - defined_vars
            if undefined_vars:
                logger.warning(f"Template uses undefined variables: {undefined_vars}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            return False
    
    def _process_variables(self, template: NotificationTemplate, variables: Dict[str, Any]) -> Dict[str, Any]:
        """处理模板变量"""
        processed = {}
        
        for var in template.variables:
            if var.name in variables:
                value = variables[var.name]
                
                # 格式化处理
                if var.format and value is not None:
                    if var.type == "date" and isinstance(value, datetime):
                        value = value.strftime(var.format)
                    elif var.type == "number" and isinstance(value, (int, float)):
                        if var.format.startswith(",."): # 千分位格式
                            value = f"{value:,.{int(var.format.split('.')[1][0])}}f"
                
                processed[var.name] = value
            elif var.default_value is not None:
                processed[var.name] = var.default_value
            elif var.required:
                logger.warning(f"Required variable '{var.name}' not provided")
                processed[var.name] = f"[{var.name}]"
        
        return processed
    
    def _validate_variable_type(self, value: Any, expected_type: str) -> bool:
        """验证变量类型"""
        if value is None:
            return True
        
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "date":
            return isinstance(value, (datetime, str))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        else:
            return True
    
    def _extract_variables_used(self, content: str) -> set:
        """提取模板中使用的变量"""
        # 匹配Jinja2变量语法 {{ variable_name }}
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'
        matches = re.findall(pattern, content)
        return set(matches)
    
    def _convert_to_html(self, content: str) -> str:
        """将文本内容转换为HTML"""
        # 简单的文本到HTML转换
        html = content.replace('\n', '<br>\n')
        
        # 添加基本HTML结构
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>通知</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .content {{ background-color: #ffffff; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        .footer {{ margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            {html}
        </div>
        <div class="footer">
            <p>此邮件由PMC生产管理系统自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        try:
            parts = version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                return f"{major}.{minor}.{patch + 1}"
            else:
                return "1.0.1"
        except:
            return "1.0.1"
    
    def export_templates(self, format: str = "json") -> str:
        """导出模板"""
        try:
            templates_data = []
            for template in self.templates.values():
                if template.is_active:
                    template_dict = asdict(template)
                    # 转换枚举为字符串
                    template_dict['type'] = template.type.value
                    template_dict['category'] = template.category.value
                    # 转换日期为字符串
                    template_dict['created_at'] = template.created_at.isoformat()
                    template_dict['updated_at'] = template.updated_at.isoformat()
                    templates_data.append(template_dict)
            
            if format == "json":
                return json.dumps(templates_data, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting templates: {e}")
            return ""
    
    def import_templates(self, data: str, format: str = "json") -> bool:
        """导入模板"""
        try:
            if format == "json":
                templates_data = json.loads(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            for template_dict in templates_data:
                # 转换字符串为枚举
                template_dict['type'] = TemplateType(template_dict['type'])
                template_dict['category'] = TemplateCategory(template_dict['category'])
                
                # 转换字符串为日期
                template_dict['created_at'] = datetime.fromisoformat(template_dict['created_at'])
                template_dict['updated_at'] = datetime.fromisoformat(template_dict['updated_at'])
                
                # 转换变量
                variables = []
                for var_dict in template_dict['variables']:
                    var = TemplateVariable(**var_dict)
                    variables.append(var)
                template_dict['variables'] = variables
                
                template = NotificationTemplate(**template_dict)
                self.add_template(template)
            
            logger.info(f"Imported {len(templates_data)} templates")
            return True
            
        except Exception as e:
            logger.error(f"Error importing templates: {e}")
            return False


# 全局模板服务实例
template_service = NotificationTemplateService()

def get_template_service() -> NotificationTemplateService:
    """获取模板服务实例"""
    return template_service