#!/usr/bin/env python3
"""微信Webhook服务启动脚本

用于启动微信API回调处理服务。
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
except ImportError:
    print("Error: uvicorn is required. Install it with: pip install uvicorn")
    sys.exit(1)

from .app import create_app


def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('webhook_service.log')
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PMC WeChat Webhook Service")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080, 
        help="Port to bind (default: 8080)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--ssl-keyfile", 
        help="SSL key file path"
    )
    parser.add_argument(
        "--ssl-certfile", 
        help="SSL certificate file path"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting PMC WeChat Webhook Service on {args.host}:{args.port}")
    
    # 检查环境变量
    required_env_vars = [
        "WECHAT_CORP_ID",
        "WECHAT_CORP_SECRET", 
        "WECHAT_AGENT_ID"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some webhook features may not work properly")
    
    # 创建应用
    app = create_app()
    
    # 配置SSL
    ssl_config = {}
    if args.ssl_keyfile and args.ssl_certfile:
        ssl_config = {
            "ssl_keyfile": args.ssl_keyfile,
            "ssl_certfile": args.ssl_certfile
        }
        logger.info("SSL enabled")
    
    try:
        # 启动服务
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            log_level=args.log_level.lower(),
            access_log=True,
            **ssl_config
        )
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()