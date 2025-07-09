#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 主程序入口
基于Creo的自然语言小家电设计系统

作者: 江门市品高电器实业有限公司
版本: 1.0.0
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config.settings import Settings
from src.core.app import AIDesignAssistant
from src.utils.logger import setup_logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="PG-Dev AI设计助理 - 基于Creo的自然语言小家电设计系统"
    )
    parser.add_argument("--dev", action="store_true", help="开发模式运行")
    parser.add_argument(
        "--config", type=str, default="config/settings.yaml", help="配置文件路径"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    parser.add_argument("--test-creo", action="store_true", help="测试Creo连接")
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志
    logger = setup_logger(
        name="ai_design_assistant",
        level=getattr(logging, args.log_level),
        dev_mode=args.dev,
    )

    try:
        # 加载配置
        settings = Settings.load_from_file(args.config)

        # 创建AI设计助理实例
        assistant = AIDesignAssistant(settings=settings, dev_mode=args.dev)

        if args.test_creo:
            # 测试Creo连接
            logger.info("正在测试Creo连接...")
            success = assistant.test_creo_connection()
            if success:
                logger.info("✅ Creo连接测试成功")
                return 0
            else:
                logger.error("❌ Creo连接测试失败")
                return 1

        # 启动AI设计助理
        logger.info("🚀 启动PG-Dev AI设计助理...")
        assistant.run()

    except KeyboardInterrupt:
        logger.info("👋 用户中断，正在退出...")
        return 0
    except Exception as e:
        logger.error(f"❌ 程序运行出错: {e}")
        if args.dev:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
