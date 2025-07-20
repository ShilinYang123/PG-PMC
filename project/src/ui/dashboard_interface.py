#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 聊天界面
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from src.utils.logger import get_logger


class MessageType(Enum):
    """消息类型"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


@dataclass
class ChatMessage:
    """聊天消息"""

    type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ChatInterface:
    """聊天界面

    提供富文本聊天界面，支持用户与AI设计助理的交互
    """

    def __init__(self, on_user_input: Callable[[str], str] = None):
        """
        Args:
            on_user_input: 用户输入处理回调函数
        """
        self.logger = get_logger(self.__class__.__name__)
        self.console = Console()

        # 消息历史
        self.messages: List[ChatMessage] = []

        # 回调函数
        self.on_user_input = on_user_input

        # 界面状态
        self.is_running = False
        self.is_processing = False

        # 配置
        self.max_history = 100
        self.show_timestamps = True
        self.auto_scroll = True

        # 样式配置
        self.styles = {
            MessageType.USER: "bold blue",
            MessageType.ASSISTANT: "bold green",
            MessageType.SYSTEM: "bold yellow",
            MessageType.ERROR: "bold red",
            MessageType.INFO: "cyan",
            MessageType.WARNING: "bold orange3",
        }

        # 命令处理器
        self.commands = {
            "/help": self._show_help,
            "/clear": self._clear_history,
            "/history": self._show_history,
            "/export": self._export_history,
            "/status": self._show_status,
            "/quit": self._quit,
            "/exit": self._quit,
        }

    def start(self):
        """启动聊天界面"""
        try:
            self.logger.info("启动聊天界面")
            self.is_running = True

            # 显示欢迎信息
            self._show_welcome()

            # 主循环
            self._main_loop()

        except KeyboardInterrupt:
            self.add_message(MessageType.INFO, "用户中断操作")
        except Exception as e:
            self.logger.error(f"聊天界面错误: {e}")
            self.add_message(MessageType.ERROR, f"界面错误: {e}")
        finally:
            self.stop()

    def stop(self):
        """停止聊天界面"""
        try:
            self.is_running = False
            self.add_message(MessageType.INFO, "聊天界面已关闭")
            self.logger.info("聊天界面已停止")

        except Exception as e:
            self.logger.error(f"停止聊天界面失败: {e}")

    def _main_loop(self):
        """主循环"""
        while self.is_running:
            try:
                # 获取用户输入
                user_input = self._get_user_input()

                if not user_input.strip():
                    continue

                # 添加用户消息
                self.add_message(MessageType.USER, user_input)

                # 检查是否为命令
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # 处理用户输入
                if self.on_user_input:
                    self._process_user_input(user_input)
                else:
                    self.add_message(
                        MessageType.WARNING, "未设置输入处理器，无法处理用户输入"
                    )

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                self.add_message(MessageType.ERROR, f"处理错误: {e}")

    def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            if self.is_processing:
                return ""

            prompt_text = "[bold blue]您[/bold blue]: "
            return Prompt.ask(prompt_text, console=self.console)

        except Exception as e:
            self.logger.error(f"获取用户输入失败: {e}")
            return ""

    def _process_user_input(self, user_input: str):
        """处理用户输入"""
        try:
            self.is_processing = True

            # 显示处理状态
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("AI正在思考...", total=None)

                # 调用处理回调
                response = self.on_user_input(user_input)

                progress.update(task, description="处理完成")

            # 添加AI回复
            if response:
                self.add_message(MessageType.ASSISTANT, response)

        except Exception as e:
            self.logger.error(f"处理用户输入失败: {e}")
            self.add_message(MessageType.ERROR, f"处理失败: {e}")
        finally:
            self.is_processing = False

    def _handle_command(self, command: str):
        """处理命令"""
        try:
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd in self.commands:
                self.commands[cmd](args)
            else:
                self.add_message(
                    MessageType.WARNING, f"未知命令: {cmd}。输入 /help 查看可用命令。"
                )

        except Exception as e:
            self.logger.error(f"处理命令失败: {e}")
            self.add_message(MessageType.ERROR, f"命令执行失败: {e}")

    def add_message(
        self, msg_type: MessageType, content: str, metadata: Dict[str, Any] = None
    ):
        """添加消息

        Args:
            msg_type: 消息类型
            content: 消息内容
            metadata: 元数据
        """
        try:
            message = ChatMessage(
                type=msg_type,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            self.messages.append(message)

            # 限制历史记录长度
            if len(self.messages) > self.max_history:
                self.messages = self.messages[-self.max_history :]

            # 显示消息
            self._display_message(message)

        except Exception as e:
            self.logger.error(f"添加消息失败: {e}")

    def _display_message(self, message: ChatMessage):
        """显示消息"""
        try:
            # 准备消息内容
            if message.type == MessageType.USER:
                prefix = "[bold blue]您[/bold blue]"
            elif message.type == MessageType.ASSISTANT:
                prefix = "[bold green]AI助理[/bold green]"
            elif message.type == MessageType.SYSTEM:
                prefix = "[bold yellow]系统[/bold yellow]"
            elif message.type == MessageType.ERROR:
                prefix = "[bold red]错误[/bold red]"
            elif message.type == MessageType.INFO:
                prefix = "[cyan]信息[/cyan]"
            elif message.type == MessageType.WARNING:
                prefix = "[bold orange3]警告[/bold orange3]"
            else:
                prefix = "[white]消息[/white]"

            # 时间戳
            timestamp = ""
            if self.show_timestamps:
                timestamp = f" [{message.timestamp.strftime('%H:%M:%S')}]"

            # 构建消息文本
            header = f"{prefix}{timestamp}: "

            # 处理长消息
            if len(message.content) > 500:
                # 使用面板显示长消息
                panel = Panel(
                    message.content,
                    title=f"{prefix.replace('[', '').replace(']', '')}{timestamp}",
                    border_style=self.styles.get(message.type, "white"),
                )
                self.console.print(panel)
            else:
                # 直接显示短消息
                self.console.print(f"{header}{message.content}")

            # 添加分隔线（对于AI回复）
            if message.type == MessageType.ASSISTANT:
                self.console.print("─" * 50, style="dim")

        except Exception as e:
            self.logger.error(f"显示消息失败: {e}")

    def _show_welcome(self):
        """显示欢迎信息"""
        try:
            welcome_panel = Panel(
                "[bold green]欢迎使用 PinGao AI设计助理![/bold green]\n\n"
                "我可以帮助您：\n"
                "• 创建3D模型和零件\n"
                "• 生成工程图\n"
                "• 优化设计参数\n"
                "• 提供设计建议\n\n"
                "输入 [bold]/help[/bold] 查看可用命令\n"
                "输入 [bold]/quit[/bold] 退出程序",
                title="AI设计助理",
                border_style="green",
            )

            self.console.print(welcome_panel)
            self.console.print()

        except Exception as e:
            self.logger.error(f"显示欢迎信息失败: {e}")

    def _show_help(self, args: List[str]):
        """显示帮助信息"""
        try:
            help_table = Table(title="可用命令")
            help_table.add_column("命令", style="cyan")
            help_table.add_column("描述", style="white")

            commands_help = [
                ("/help", "显示此帮助信息"),
                ("/clear", "清空聊天历史"),
                ("/history", "显示聊天历史"),
                ("/export [文件名]", "导出聊天历史到文件"),
                ("/status", "显示系统状态"),
                ("/quit, /exit", "退出程序"),
            ]

            for cmd, desc in commands_help:
                help_table.add_row(cmd, desc)

            self.console.print(help_table)

        except Exception as e:
            self.logger.error(f"显示帮助失败: {e}")
            self.add_message(MessageType.ERROR, f"显示帮助失败: {e}")

    def _clear_history(self, args: List[str]):
        """清空历史记录"""
        try:
            self.messages.clear()
            self.console.clear()
            self.add_message(MessageType.INFO, "聊天历史已清空")

        except Exception as e:
            self.logger.error(f"清空历史失败: {e}")
            self.add_message(MessageType.ERROR, f"清空历史失败: {e}")

    def _show_history(self, args: List[str]):
        """显示历史记录"""
        try:
            if not self.messages:
                self.add_message(MessageType.INFO, "暂无聊天历史")
                return

            # 限制显示数量
            limit = 10
            if args and args[0].isdigit():
                limit = min(int(args[0]), len(self.messages))

            history_messages = self.messages[-limit:]

            history_panel = Panel(
                "\n".join(
                    [
                        f"[{msg.timestamp.strftime('%H:%M:%S')}] "
                        f"{msg.type.value}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}"
                        for msg in history_messages
                    ]
                ),
                title=f"最近 {len(history_messages)} 条消息",
                border_style="cyan",
            )

            self.console.print(history_panel)

        except Exception as e:
            self.logger.error(f"显示历史失败: {e}")
            self.add_message(MessageType.ERROR, f"显示历史失败: {e}")

    def _export_history(self, args: List[str]):
        """导出历史记录"""
        try:
            if not self.messages:
                self.add_message(MessageType.WARNING, "暂无聊天历史可导出")
                return

            # 确定文件名
            filename = "chat_history.txt"
            if args:
                filename = args[0]
                if not filename.endswith(".txt"):
                    filename += ".txt"

            # 导出内容
            export_lines = [
                "# PinGao AI设计助理 - 聊天历史",
                f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"消息总数: {len(self.messages)}",
                "",
                "=" * 50,
                "",
            ]

            for msg in self.messages:
                export_lines.extend(
                    [
                        f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {msg.type.value.upper()}",
                        msg.content,
                        "-" * 30,
                        "",
                    ]
                )

            # 写入文件
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(export_lines))

            self.add_message(MessageType.INFO, f"聊天历史已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出历史失败: {e}")
            self.add_message(MessageType.ERROR, f"导出历史失败: {e}")

    def _show_status(self, args: List[str]):
        """显示状态信息"""
        try:
            status_table = Table(title="系统状态")
            status_table.add_column("项目", style="cyan")
            status_table.add_column("状态", style="white")

            status_items = [
                ("界面状态", "运行中" if self.is_running else "已停止"),
                ("处理状态", "处理中" if self.is_processing else "空闲"),
                ("消息数量", str(len(self.messages))),
                ("最大历史", str(self.max_history)),
                ("显示时间戳", "是" if self.show_timestamps else "否"),
            ]

            for item, status in status_items:
                status_table.add_row(item, status)

            self.console.print(status_table)

        except Exception as e:
            self.logger.error(f"显示状态失败: {e}")
            self.add_message(MessageType.ERROR, f"显示状态失败: {e}")

    def _quit(self, args: List[str]):
        """退出程序"""
        try:
            self.add_message(MessageType.INFO, "正在退出...")
            self.is_running = False

        except Exception as e:
            self.logger.error(f"退出失败: {e}")

    def set_config(self, **kwargs):
        """设置配置

        Args:
            **kwargs: 配置参数
        """
        try:
            if "max_history" in kwargs:
                self.max_history = kwargs["max_history"]

            if "show_timestamps" in kwargs:
                self.show_timestamps = kwargs["show_timestamps"]

            if "auto_scroll" in kwargs:
                self.auto_scroll = kwargs["auto_scroll"]

            self.logger.info("聊天界面配置已更新")

        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")

    def get_history(self) -> List[ChatMessage]:
        """获取聊天历史

        Returns:
            List[ChatMessage]: 聊天历史
        """
        return self.messages.copy()

    def clear_history(self):
        """清空聊天历史"""
        self.messages.clear()
        self.logger.info("聊天历史已清空")