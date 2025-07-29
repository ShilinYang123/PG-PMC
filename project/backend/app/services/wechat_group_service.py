"""微信群组管理服务

实现企业微信群组管理功能，包括：
- 群组创建和管理
- 成员管理
- 群组消息发送
- 群组信息查询
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import asyncio


class GroupType(Enum):
    """群组类型"""
    PRODUCTION = "production"  # 生产群组
    MANAGEMENT = "management"  # 管理群组
    NOTIFICATION = "notification"  # 通知群组
    PROJECT = "project"  # 项目群组
    DEPARTMENT = "department"  # 部门群组


@dataclass
class GroupMember:
    """群组成员"""
    user_id: str
    name: str
    department: str
    role: str  # owner, admin, member
    join_time: datetime
    is_active: bool = True


@dataclass
class GroupInfo:
    """群组信息"""
    group_id: str
    name: str
    description: str
    group_type: GroupType
    owner_id: str
    admin_ids: List[str]
    member_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    settings: Dict = None


@dataclass
class GroupMessage:
    """群组消息"""
    message_id: str
    group_id: str
    sender_id: str
    content: str
    message_type: str  # text, image, file, card
    sent_at: datetime
    read_count: int = 0
    reply_count: int = 0


class WeChatGroupService:
    """微信群组服务"""
    
    def __init__(self, corp_id: str, corp_secret: str, agent_id: str):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.access_token = None
        self.token_expires_at = None
        self.groups: Dict[str, GroupInfo] = {}
        self.group_members: Dict[str, List[GroupMember]] = {}
        self.group_messages: Dict[str, List[GroupMessage]] = {}
        
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        if (self.access_token and 
            self.token_expires_at and 
            datetime.now() < self.token_expires_at):
            return self.access_token
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data["access_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 600)
                logger.info("微信访问令牌获取成功")
                return self.access_token
            else:
                logger.error(f"获取微信访问令牌失败: {data}")
                raise Exception(f"获取访问令牌失败: {data.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"获取微信访问令牌异常: {e}")
            raise
    
    async def create_group(self, name: str, description: str, 
                          group_type: GroupType, owner_id: str,
                          initial_members: List[str] = None) -> str:
        """创建群组"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/create?access_token={access_token}"
            
            # 构建群组数据
            group_data = {
                "name": name,
                "owner": owner_id,
                "userlist": initial_members or [owner_id],
                "chatid": f"{group_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = requests.post(url, json=group_data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                group_id = result["chatid"]
                
                # 保存群组信息
                group_info = GroupInfo(
                    group_id=group_id,
                    name=name,
                    description=description,
                    group_type=group_type,
                    owner_id=owner_id,
                    admin_ids=[],
                    member_count=len(initial_members or [owner_id]),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                self.groups[group_id] = group_info
                
                # 初始化成员列表
                members = []
                for user_id in (initial_members or [owner_id]):
                    member = GroupMember(
                        user_id=user_id,
                        name=await self._get_user_name(user_id),
                        department=await self._get_user_department(user_id),
                        role="owner" if user_id == owner_id else "member",
                        join_time=datetime.now()
                    )
                    members.append(member)
                
                self.group_members[group_id] = members
                self.group_messages[group_id] = []
                
                logger.info(f"群组创建成功: {group_id} - {name}")
                return group_id
            else:
                logger.error(f"群组创建失败: {result}")
                raise Exception(f"群组创建失败: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"创建群组异常: {e}")
            raise
    
    async def add_members(self, group_id: str, user_ids: List[str]) -> bool:
        """添加群组成员"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/update?access_token={access_token}"
            
            # 获取当前成员列表
            current_members = [m.user_id for m in self.group_members.get(group_id, [])]
            new_members = list(set(current_members + user_ids))
            
            data = {
                "chatid": group_id,
                "add_user_list": user_ids
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                # 更新本地成员列表
                for user_id in user_ids:
                    if user_id not in current_members:
                        member = GroupMember(
                            user_id=user_id,
                            name=await self._get_user_name(user_id),
                            department=await self._get_user_department(user_id),
                            role="member",
                            join_time=datetime.now()
                        )
                        self.group_members[group_id].append(member)
                
                # 更新群组信息
                if group_id in self.groups:
                    self.groups[group_id].member_count = len(self.group_members[group_id])
                    self.groups[group_id].updated_at = datetime.now()
                
                logger.info(f"群组成员添加成功: {group_id}, 新增 {len(user_ids)} 人")
                return True
            else:
                logger.error(f"添加群组成员失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"添加群组成员异常: {e}")
            return False
    
    async def remove_members(self, group_id: str, user_ids: List[str]) -> bool:
        """移除群组成员"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/update?access_token={access_token}"
            
            data = {
                "chatid": group_id,
                "del_user_list": user_ids
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                # 更新本地成员列表
                if group_id in self.group_members:
                    self.group_members[group_id] = [
                        m for m in self.group_members[group_id] 
                        if m.user_id not in user_ids
                    ]
                
                # 更新群组信息
                if group_id in self.groups:
                    self.groups[group_id].member_count = len(self.group_members[group_id])
                    self.groups[group_id].updated_at = datetime.now()
                
                logger.info(f"群组成员移除成功: {group_id}, 移除 {len(user_ids)} 人")
                return True
            else:
                logger.error(f"移除群组成员失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"移除群组成员异常: {e}")
            return False
    
    async def send_group_message(self, group_id: str, content: str, 
                                message_type: str = "text") -> bool:
        """发送群组消息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/send?access_token={access_token}"
            
            data = {
                "chatid": group_id,
                "msgtype": message_type,
                message_type: {
                    "content": content
                }
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                # 记录消息
                message = GroupMessage(
                    message_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    group_id=group_id,
                    sender_id="system",
                    content=content,
                    message_type=message_type,
                    sent_at=datetime.now()
                )
                
                if group_id not in self.group_messages:
                    self.group_messages[group_id] = []
                self.group_messages[group_id].append(message)
                
                logger.info(f"群组消息发送成功: {group_id}")
                return True
            else:
                logger.error(f"群组消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送群组消息异常: {e}")
            return False
    
    async def get_group_info(self, group_id: str) -> Optional[GroupInfo]:
        """获取群组信息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/get?access_token={access_token}&chatid={group_id}"
            
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                chat_info = result["chat_info"]
                
                # 更新本地群组信息
                if group_id in self.groups:
                    self.groups[group_id].name = chat_info["name"]
                    self.groups[group_id].member_count = len(chat_info["userlist"])
                    self.groups[group_id].updated_at = datetime.now()
                
                return self.groups.get(group_id)
            else:
                logger.error(f"获取群组信息失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取群组信息异常: {e}")
            return None
    
    async def get_group_members(self, group_id: str) -> List[GroupMember]:
        """获取群组成员列表"""
        return self.group_members.get(group_id, [])
    
    async def get_group_messages(self, group_id: str, limit: int = 50) -> List[GroupMessage]:
        """获取群组消息历史"""
        messages = self.group_messages.get(group_id, [])
        return messages[-limit:] if limit > 0 else messages
    
    async def update_group_info(self, group_id: str, name: str = None, 
                               description: str = None) -> bool:
        """更新群组信息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/update?access_token={access_token}"
            
            data = {"chatid": group_id}
            if name:
                data["name"] = name
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                # 更新本地信息
                if group_id in self.groups:
                    if name:
                        self.groups[group_id].name = name
                    if description:
                        self.groups[group_id].description = description
                    self.groups[group_id].updated_at = datetime.now()
                
                logger.info(f"群组信息更新成功: {group_id}")
                return True
            else:
                logger.error(f"更新群组信息失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"更新群组信息异常: {e}")
            return False
    
    async def set_group_admin(self, group_id: str, user_id: str) -> bool:
        """设置群组管理员"""
        if group_id in self.groups and group_id in self.group_members:
            # 更新成员角色
            for member in self.group_members[group_id]:
                if member.user_id == user_id:
                    member.role = "admin"
                    break
            
            # 更新群组管理员列表
            if user_id not in self.groups[group_id].admin_ids:
                self.groups[group_id].admin_ids.append(user_id)
            
            logger.info(f"设置群组管理员成功: {group_id} - {user_id}")
            return True
        
        return False
    
    async def remove_group_admin(self, group_id: str, user_id: str) -> bool:
        """移除群组管理员"""
        if group_id in self.groups and group_id in self.group_members:
            # 更新成员角色
            for member in self.group_members[group_id]:
                if member.user_id == user_id:
                    member.role = "member"
                    break
            
            # 更新群组管理员列表
            if user_id in self.groups[group_id].admin_ids:
                self.groups[group_id].admin_ids.remove(user_id)
            
            logger.info(f"移除群组管理员成功: {group_id} - {user_id}")
            return True
        
        return False
    
    async def delete_group(self, group_id: str) -> bool:
        """删除群组"""
        try:
            # 企业微信API不直接支持删除群组，只能通过移除所有成员来实现
            if group_id in self.group_members:
                all_members = [m.user_id for m in self.group_members[group_id]]
                if all_members:
                    await self.remove_members(group_id, all_members)
            
            # 删除本地数据
            if group_id in self.groups:
                self.groups[group_id].is_active = False
                del self.groups[group_id]
            
            if group_id in self.group_members:
                del self.group_members[group_id]
            
            if group_id in self.group_messages:
                del self.group_messages[group_id]
            
            logger.info(f"群组删除成功: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除群组异常: {e}")
            return False
    
    def get_all_groups(self) -> List[GroupInfo]:
        """获取所有群组"""
        return [group for group in self.groups.values() if group.is_active]
    
    def get_groups_by_type(self, group_type: GroupType) -> List[GroupInfo]:
        """按类型获取群组"""
        return [group for group in self.groups.values() 
                if group.group_type == group_type and group.is_active]
    
    async def _get_user_name(self, user_id: str) -> str:
        """获取用户姓名（模拟实现）"""
        # 实际实现中应该调用企业微信API获取用户信息
        return f"用户_{user_id}"
    
    async def _get_user_department(self, user_id: str) -> str:
        """获取用户部门（模拟实现）"""
        # 实际实现中应该调用企业微信API获取用户部门信息
        return "未知部门"
    
    def get_group_statistics(self) -> Dict:
        """获取群组统计信息"""
        total_groups = len([g for g in self.groups.values() if g.is_active])
        total_members = sum(g.member_count for g in self.groups.values() if g.is_active)
        total_messages = sum(len(msgs) for msgs in self.group_messages.values())
        
        group_types = {}
        for group in self.groups.values():
            if group.is_active:
                group_type = group.group_type.value
                group_types[group_type] = group_types.get(group_type, 0) + 1
        
        return {
            'total_groups': total_groups,
            'total_members': total_members,
            'total_messages': total_messages,
            'group_types': group_types,
            'average_members_per_group': round(total_members / total_groups, 2) if total_groups > 0 else 0
        }