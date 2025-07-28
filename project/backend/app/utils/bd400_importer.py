from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
import re
from sqlalchemy.orm import Session
from ..models.order import Order, OrderStatus, OrderPriority
from ..schemas.order import OrderCreate
import logging

logger = logging.getLogger(__name__)

class BD400OrderImporter:
    """BD400订单表导入处理器"""
    
    # BD400订单表字段映射
    FIELD_MAPPING = {
        '订单号': 'order_number',
        '客户名称': 'customer_name', 
        '客户代码': 'customer_code',
        '产品名称': 'product_name',
        '产品型号': 'product_model',
        '产品规格': 'product_spec',
        '数量': 'quantity',
        '单位': 'unit',
        '单价': 'unit_price',
        '总金额': 'total_amount',
        '币种': 'currency',
        '下单日期': 'order_date',
        '交货日期': 'delivery_date',
        '优先级': 'priority',
        '联系人': 'contact_person',
        '联系电话': 'contact_phone',
        '联系邮箱': 'contact_email',
        '交货地址': 'delivery_address',
        '技术要求': 'technical_requirements',
        '质量标准': 'quality_standards',
        '备注': 'remark'
    }
    
    # 优先级映射
    PRIORITY_MAPPING = {
        '低': OrderPriority.LOW,
        '中': OrderPriority.MEDIUM,
        '高': OrderPriority.HIGH,
        '紧急': OrderPriority.URGENT,
        'LOW': OrderPriority.LOW,
        'MEDIUM': OrderPriority.MEDIUM,
        'HIGH': OrderPriority.HIGH,
        'URGENT': OrderPriority.URGENT
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.errors = []
        self.warnings = []
        
    def import_from_excel(self, file_content: bytes) -> Dict[str, Any]:
        """从Excel文件导入BD400订单数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_content, sheet_name=0)
            
            # 数据预处理
            df = self._preprocess_dataframe(df)
            
            # 验证数据格式
            validation_result = self._validate_dataframe(df)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': '数据验证失败',
                    'errors': validation_result['errors'],
                    'imported_count': 0
                }
            
            # 导入数据
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    result = self._import_single_order(row, index + 2)  # +2因为Excel行号从1开始，且有表头
                    if result['success']:
                        imported_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    self.errors.append(f"第{index + 2}行: 导入失败 - {str(e)}")
                    skipped_count += 1
            
            # 提交事务
            if imported_count > 0:
                self.db.commit()
                logger.info(f"BD400订单导入完成: 成功{imported_count}条, 跳过{skipped_count}条")
            
            return {
                'success': True,
                'message': f'导入完成: 成功{imported_count}条, 跳过{skipped_count}条',
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"BD400订单导入失败: {str(e)}")
            return {
                'success': False,
                'message': f'导入失败: {str(e)}',
                'imported_count': 0,
                'errors': [str(e)]
            }
    
    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 删除空行
        df = df.dropna(how='all')
        
        # 重命名列
        df = df.rename(columns=self.FIELD_MAPPING)
        
        # 处理日期格式
        date_columns = ['order_date', 'delivery_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 处理数值格式
        numeric_columns = ['quantity', 'unit_price', 'total_amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理字符串格式
        string_columns = ['order_number', 'customer_name', 'product_name']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """验证数据格式"""
        errors = []
        
        # 检查必要字段
        required_fields = ['order_number', 'customer_name', 'product_name', 'quantity', 'delivery_date']
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        if missing_fields:
            errors.append(f"缺少必要字段: {', '.join(missing_fields)}")
        
        # 检查数据完整性
        for index, row in df.iterrows():
            row_num = index + 2
            
            # 检查订单号
            if pd.isna(row.get('order_number')) or str(row.get('order_number')).strip() == '':
                errors.append(f"第{row_num}行: 订单号不能为空")
            
            # 检查客户名称
            if pd.isna(row.get('customer_name')) or str(row.get('customer_name')).strip() == '':
                errors.append(f"第{row_num}行: 客户名称不能为空")
            
            # 检查产品名称
            if pd.isna(row.get('product_name')) or str(row.get('product_name')).strip() == '':
                errors.append(f"第{row_num}行: 产品名称不能为空")
            
            # 检查数量
            if pd.isna(row.get('quantity')) or row.get('quantity') <= 0:
                errors.append(f"第{row_num}行: 数量必须大于0")
            
            # 检查交货日期
            if pd.isna(row.get('delivery_date')):
                errors.append(f"第{row_num}行: 交货日期不能为空")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _import_single_order(self, row: pd.Series, row_num: int) -> Dict[str, Any]:
        """导入单个订单"""
        try:
            # 检查订单是否已存在
            order_number = str(row.get('order_number')).strip()
            existing_order = self.db.query(Order).filter(
                Order.order_no == order_number
            ).first()
            
            if existing_order:
                self.warnings.append(f"第{row_num}行: 订单号 {order_number} 已存在，跳过")
                return {'success': False, 'reason': 'duplicate'}
            
            # 构建订单数据
            order_data = self._build_order_data(row)
            
            # 创建订单
            order = Order(**order_data)
            self.db.add(order)
            
            return {'success': True}
            
        except Exception as e:
            self.errors.append(f"第{row_num}行: {str(e)}")
            return {'success': False, 'reason': str(e)}
    
    def _build_order_data(self, row: pd.Series) -> Dict[str, Any]:
        """构建订单数据"""
        data = {
            'order_no': str(row.get('order_number', '')).strip(),
            'customer_name': str(row.get('customer_name', '')).strip(),
            'product_name': str(row.get('product_name', '')).strip(),
            'quantity': int(row.get('quantity', 0)),
            'unit': str(row.get('unit', '件')).strip(),
            'order_date': self._parse_date(row.get('order_date'), datetime.now().date()),
            'delivery_date': self._parse_date(row.get('delivery_date')),
            'status': OrderStatus.PENDING,
            'priority': self._parse_priority(row.get('priority')),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # 可选字段
        optional_fields = {
            'product_model': 'product_model',
            'contact_person': 'contact_person',
            'contact_phone': 'contact_phone', 
            'contact_email': 'contact_email',
            'delivery_address': 'delivery_address',
            'technical_requirements': 'technical_requirements',
            'quality_standards': 'quality_standards',
            'remark': 'remark'
        }
        
        for field, column in optional_fields.items():
            value = row.get(column)
            if pd.notna(value) and str(value).strip():
                data[field] = str(value).strip()
        
        # 数值字段
        if pd.notna(row.get('unit_price')):
            data['unit_price'] = float(row.get('unit_price'))
        
        if pd.notna(row.get('total_amount')):
            data['total_amount'] = float(row.get('total_amount'))
        
        return data
    
    def _parse_date(self, date_value, default=None) -> date:
        """解析日期"""
        if pd.isna(date_value):
            if default is not None:
                return default
            raise ValueError("日期不能为空")
        
        if isinstance(date_value, pd.Timestamp):
            return date_value.date()
        elif isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, date):
            return date_value
        else:
            # 尝试解析字符串日期
            try:
                return pd.to_datetime(str(date_value)).date()
            except:
                raise ValueError(f"无效的日期格式: {date_value}")
    
    def _parse_priority(self, priority_value) -> OrderPriority:
        """解析优先级"""
        if pd.isna(priority_value):
            return OrderPriority.MEDIUM
        
        priority_str = str(priority_value).strip()
        return self.PRIORITY_MAPPING.get(priority_str, OrderPriority.MEDIUM)