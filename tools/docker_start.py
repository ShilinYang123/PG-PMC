#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker环境专用启动脚本
简化版本，专门用于容器化环境
"""

import os
import sys
import time
from pathlib import Path

def main():
    """Docker环境主启动函数"""
    print("🐳 Docker环境启动中...")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查基本环境
    try:
        import flask
        print(f"✅ Flask版本: {flask.__version__}")
    except ImportError:
        print("❌ Flask未安装")
        return 1
    
    try:
        import yaml
        print(f"✅ PyYAML已安装")
    except ImportError:
        print("❌ PyYAML未安装")
        return 1
    
    # 启动简单的Web服务
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            'status': 'running',
            'service': 'PMC Docker Environment',
            'timestamp': time.time(),
            'environment': os.environ.get('ENV', 'production')
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    print("🚀 启动Web服务...")
    print("📡 服务地址: http://0.0.0.0:8000")
    
    # 启动服务
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=os.environ.get('ENV') == 'development'
    )
    
    return 0

if __name__ == '__main__':
    sys.exit(main())