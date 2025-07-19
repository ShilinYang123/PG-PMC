#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC智能追踪系统 - IoT设备管理器
"""

import json
import time
from typing import Dict, List, Optional, Any
from threading import Thread, Event

import paho.mqtt.client as mqtt
from src.utils.logger import get_logger


class IoTDeviceManager:
    """IoT设备管理器"""

    def __init__(self, mqtt_config: Dict[str, Any], database=None):
        """初始化IoT设备管理器

        Args:
            mqtt_config: MQTT配置
            database: 数据库连接器
        """
        self.mqtt_config = mqtt_config
        self.database = database
        self.logger = get_logger(self.__class__.__name__)
        
        # MQTT客户端
        self.mqtt_client = None
        self.connected = False
        
        # 设备状态
        self.devices: Dict[str, Dict] = {}
        self.device_data: Dict[str, List] = {}
        
        # 线程控制
        self.stop_event = Event()
        self.monitor_thread = None
        
    def initialize(self) -> bool:
        """初始化IoT设备管理器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化IoT设备管理器...")
            
            # 初始化MQTT客户端
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.username_pw_set(
                self.mqtt_config['username'],
                self.mqtt_config['password']
            )
            
            # 设置回调函数
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_disconnect = self._on_disconnect
            
            # 连接MQTT代理
            self.mqtt_client.connect(
                self.mqtt_config['host'],
                self.mqtt_config['port'],
                60
            )
            
            # 启动MQTT循环
            self.mqtt_client.loop_start()
            
            # 启动监控线程
            self.monitor_thread = Thread(target=self._monitor_devices)
            self.monitor_thread.start()
            
            self.logger.info("✅ IoT设备管理器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ IoT设备管理器初始化失败: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            self.logger.info("✅ MQTT连接成功")
            
            # 订阅设备主题
            for topic in self.mqtt_config.get('topics', []):
                client.subscribe(topic)
                self.logger.info(f"订阅主题: {topic}")
        else:
            self.logger.error(f"❌ MQTT连接失败，错误码: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """MQTT消息回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            self.logger.debug(f"收到消息 - 主题: {topic}, 数据: {payload}")
            
            # 解析设备ID
            device_id = self._extract_device_id(topic)
            if device_id:
                self._update_device_data(device_id, payload)
                
        except Exception as e:
            self.logger.error(f"处理MQTT消息失败: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.connected = False
        self.logger.warning(f"MQTT连接断开，错误码: {rc}")
    
    def _extract_device_id(self, topic: str) -> Optional[str]:
        """从主题中提取设备ID"""
        # 假设主题格式为: devices/{device_id}/data
        parts = topic.split('/')
        if len(parts) >= 2 and parts[0] == 'devices':
            return parts[1]
        return None
    
    def _update_device_data(self, device_id: str, data: Dict):
        """更新设备数据"""
        timestamp = time.time()
        
        # 更新设备状态
        if device_id not in self.devices:
            self.devices[device_id] = {
                'id': device_id,
                'status': 'online',
                'last_seen': timestamp,
                'data_count': 0
            }
        
        self.devices[device_id]['last_seen'] = timestamp
        self.devices[device_id]['data_count'] += 1
        
        # 存储设备数据
        if device_id not in self.device_data:
            self.device_data[device_id] = []
        
        data_entry = {
            'timestamp': timestamp,
            'data': data
        }
        
        self.device_data[device_id].append(data_entry)
        
        # 限制数据历史长度
        if len(self.device_data[device_id]) > 1000:
            self.device_data[device_id] = self.device_data[device_id][-1000:]
        
        # 保存到数据库
        if self.database:
            try:
                self.database.save_device_data(device_id, data_entry)
            except Exception as e:
                self.logger.error(f"保存设备数据到数据库失败: {e}")
    
    def _monitor_devices(self):
        """监控设备状态"""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # 检查设备离线状态
                for device_id, device in self.devices.items():
                    if current_time - device['last_seen'] > 300:  # 5分钟无数据认为离线
                        if device['status'] != 'offline':
                            device['status'] = 'offline'
                            self.logger.warning(f"设备 {device_id} 离线")
                    else:
                        if device['status'] != 'online':
                            device['status'] = 'online'
                            self.logger.info(f"设备 {device_id} 上线")
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                self.logger.error(f"设备监控错误: {e}")
                time.sleep(10)
    
    def get_device_list(self) -> List[Dict]:
        """获取设备列表"""
        return list(self.devices.values())
    
    def get_device_data(self, device_id: str, limit: int = 100) -> List[Dict]:
        """获取设备数据"""
        if device_id in self.device_data:
            return self.device_data[device_id][-limit:]
        return []
    
    def send_command(self, device_id: str, command: Dict) -> bool:
        """向设备发送命令"""
        try:
            if not self.connected:
                self.logger.error("MQTT未连接，无法发送命令")
                return False
            
            topic = f"devices/{device_id}/commands"
            payload = json.dumps(command)
            
            self.mqtt_client.publish(topic, payload)
            self.logger.info(f"向设备 {device_id} 发送命令: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送设备命令失败: {e}")
            return False
    
    def stop(self):
        """停止IoT设备管理器"""
        self.logger.info("正在停止IoT设备管理器...")
        
        # 停止监控线程
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join()
        
        # 断开MQTT连接
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        self.logger.info("IoT设备管理器已停止")