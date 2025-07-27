from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import re
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """数据验证错误"""
    pass


class DataValidator:
    """
    数据验证工具类
    """
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """
        验证必填字段
        
        Args:
            value: 要验证的值
            field_name: 字段名称
        
        Returns:
            Any: 验证后的值
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(f"{field_name} 是必填字段")
        return value
    
    @staticmethod
    def validate_string(value: Any, field_name: str, 
                       min_length: int = 0, max_length: int = None,
                       pattern: str = None) -> str:
        """
        验证字符串
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            min_length: 最小长度
            max_length: 最大长度
            pattern: 正则表达式模式
        
        Returns:
            str: 验证后的字符串
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} 长度不能少于 {min_length} 个字符")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"{field_name} 长度不能超过 {max_length} 个字符")
        
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"{field_name} 格式不正确")
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, field_name: str,
                        min_value: int = None, max_value: int = None) -> int:
        """
        验证整数
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值
        
        Returns:
            int: 验证后的整数
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return None
            
            int_value = int(float(value))  # 先转float再转int，处理"1.0"这种情况
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} 必须是整数")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} 不能小于 {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} 不能大于 {max_value}")
        
        return int_value
    
    @staticmethod
    def validate_float(value: Any, field_name: str,
                      min_value: float = None, max_value: float = None,
                      decimal_places: int = None) -> float:
        """
        验证浮点数
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值
            decimal_places: 小数位数
        
        Returns:
            float: 验证后的浮点数
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return None
            
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} 必须是数字")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} 不能小于 {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} 不能大于 {max_value}")
        
        if decimal_places is not None:
            try:
                decimal_value = Decimal(str(float_value))
                if decimal_value.as_tuple().exponent < -decimal_places:
                    raise ValidationError(f"{field_name} 小数位数不能超过 {decimal_places} 位")
            except InvalidOperation:
                raise ValidationError(f"{field_name} 数字格式不正确")
        
        return float_value
    
    @staticmethod
    def validate_date(value: Any, field_name: str,
                     date_format: str = "%Y-%m-%d") -> date:
        """
        验证日期
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            date_format: 日期格式
        
        Returns:
            date: 验证后的日期
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                # 尝试其他常见格式
                formats = ["%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y年%m月%d日"]
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                
                raise ValidationError(f"{field_name} 日期格式不正确，请使用 YYYY-MM-DD 格式")
        
        raise ValidationError(f"{field_name} 必须是日期类型")
    
    @staticmethod
    def validate_datetime(value: Any, field_name: str,
                         datetime_format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """
        验证日期时间
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            datetime_format: 日期时间格式
        
        Returns:
            datetime: 验证后的日期时间
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            
            try:
                return datetime.strptime(value, datetime_format)
            except ValueError:
                # 尝试其他常见格式
                formats = [
                    "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y",
                    "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M",
                    "%Y年%m月%d日", "%Y年%m月%d日 %H:%M:%S"
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                
                raise ValidationError(f"{field_name} 日期时间格式不正确")
        
        raise ValidationError(f"{field_name} 必须是日期时间类型")
    
    @staticmethod
    def validate_email(value: Any, field_name: str) -> str:
        """
        验证邮箱地址
        
        Args:
            value: 要验证的值
            field_name: 字段名称
        
        Returns:
            str: 验证后的邮箱地址
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip().lower()
        
        if value == "":
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError(f"{field_name} 邮箱格式不正确")
        
        return value
    
    @staticmethod
    def validate_phone(value: Any, field_name: str) -> str:
        """
        验证手机号码
        
        Args:
            value: 要验证的值
            field_name: 字段名称
        
        Returns:
            str: 验证后的手机号码
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if value == "":
            return None
        
        # 移除常见的分隔符
        value = re.sub(r'[\s\-\(\)]', '', value)
        
        # 中国手机号码格式
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, value):
            raise ValidationError(f"{field_name} 手机号码格式不正确")
        
        return value
    
    @staticmethod
    def validate_choice(value: Any, field_name: str, choices: List[Any]) -> Any:
        """
        验证选择项
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            choices: 可选择的值列表
        
        Returns:
            Any: 验证后的值
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if value not in choices:
            raise ValidationError(f"{field_name} 必须是以下值之一: {', '.join(map(str, choices))}")
        
        return value
    
    @staticmethod
    def validate_unique(value: Any, field_name: str, existing_values: List[Any]) -> Any:
        """
        验证唯一性
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            existing_values: 已存在的值列表
        
        Returns:
            Any: 验证后的值
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            return None
        
        if value in existing_values:
            raise ValidationError(f"{field_name} '{value}' 已存在")
        
        return value
    
    @staticmethod
    def validate_batch(data: Dict[str, Any], 
                      validation_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量验证数据
        
        Args:
            data: 要验证的数据字典
            validation_rules: 验证规则字典
        
        Returns:
            Dict[str, Any]: 验证后的数据
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        validated_data = {}
        errors = []
        
        for field_name, rules in validation_rules.items():
            try:
                value = data.get(field_name)
                
                # 必填验证
                if rules.get('required', False):
                    value = DataValidator.validate_required(value, field_name)
                
                # 类型验证
                field_type = rules.get('type')
                if field_type and value is not None:
                    if field_type == 'string':
                        value = DataValidator.validate_string(
                            value, field_name,
                            min_length=rules.get('min_length', 0),
                            max_length=rules.get('max_length'),
                            pattern=rules.get('pattern')
                        )
                    elif field_type == 'integer':
                        value = DataValidator.validate_integer(
                            value, field_name,
                            min_value=rules.get('min_value'),
                            max_value=rules.get('max_value')
                        )
                    elif field_type == 'float':
                        value = DataValidator.validate_float(
                            value, field_name,
                            min_value=rules.get('min_value'),
                            max_value=rules.get('max_value'),
                            decimal_places=rules.get('decimal_places')
                        )
                    elif field_type == 'date':
                        value = DataValidator.validate_date(
                            value, field_name,
                            date_format=rules.get('date_format', '%Y-%m-%d')
                        )
                    elif field_type == 'datetime':
                        value = DataValidator.validate_datetime(
                            value, field_name,
                            datetime_format=rules.get('datetime_format', '%Y-%m-%d %H:%M:%S')
                        )
                    elif field_type == 'email':
                        value = DataValidator.validate_email(value, field_name)
                    elif field_type == 'phone':
                        value = DataValidator.validate_phone(value, field_name)
                
                # 选择项验证
                choices = rules.get('choices')
                if choices and value is not None:
                    value = DataValidator.validate_choice(value, field_name, choices)
                
                validated_data[field_name] = value
                
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError('; '.join(errors))
        
        return validated_data


# 创建全局实例
data_validator = DataValidator()