#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的配置迁移脚本
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# 添加项目src目录到路径
project_root = Path(__file__).parent.parent.parent
project_src = project_root / "src"
sys.path.insert(0, str(project_src))

try:
    from core.config_center import ConfigCenter, get_config_center
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


def scan_config_files(directory: Path) -> List[Dict[str, Any]]:
    """扫描配置文件"""
    config_files = []

    # 扫描常见的配置文件
    patterns = [
        "*.yaml",
        "*.yml",
        "*.json",
        "*.ini",
        "*.cfg",
        "*.conf",
        ".env*",
        "config.*",
        "settings.*",
    ]

    for pattern in patterns:
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                config_files.append(
                    {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix or "unknown",
                    }
                )

    return config_files


def load_config_file(file_path: Path) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        if file_path.suffix in [".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        elif file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif file_path.name.startswith(".env"):
            # 简单的.env文件解析
            env_config = {}
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_config[key.strip()] = value.strip().strip("\"'")
            return env_config
        else:
            print(f"⚠️ 不支持的配置文件格式: {file_path}")
            return {}
    except Exception as e:
        print(f"❌ 加载配置文件失败 {file_path}: {e}")
        return {}


def main():
    """主函数"""
    print("=== 配置文件迁移工具 ===")
    print(f"项目根目录: {project_root}")

    # 扫描配置文件
    print("\n📁 扫描配置文件...")
    config_files = scan_config_files(project_root)

    if not config_files:
        print("❌ 未找到任何配置文件")
        return

    print(f"✅ 找到 {len(config_files)} 个配置文件:")
    for config_file in config_files:
        print(
            f"  - {config_file['name']} ({config_file['type']}) - {config_file['size']} bytes"
        )
        print(f"    路径: {config_file['path']}")

    # 创建配置中心
    print("\n🔧 创建配置中心...")
    config_center = ConfigCenter(project_root)

    # 合并配置
    print("\n🔄 合并配置文件...")
    merged_config = {}

    for config_file in config_files:
        file_path = Path(config_file["path"])
        print(f"处理: {file_path.name}")

        config_data = load_config_file(file_path)
        if config_data:
            # 检查配置数据类型
            if isinstance(config_data, dict):
                # 简单的配置合并
                for key, value in config_data.items():
                    if key not in merged_config:
                        merged_config[key] = value
                    else:
                        print(f"  ⚠️ 配置冲突: {key} (保留现有值)")
            elif isinstance(config_data, list):
                # 如果是列表，使用文件名作为键
                file_key = file_path.stem
                if file_key not in merged_config:
                    merged_config[file_key] = config_data
                else:
                    print(f"  ⚠️ 配置冲突: {file_key} (保留现有值)")
            else:
                print(f"  ⚠️ 不支持的配置数据类型: {type(config_data)}")

    print(f"✅ 合并完成，共 {len(merged_config)} 个配置项")

    # 保存到统一配置
    print("\n💾 保存统一配置...")
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)

    # 保存为YAML格式
    unified_config_path = config_dir / "unified_settings.yaml"
    try:
        with open(unified_config_path, "w", encoding="utf-8") as f:
            yaml.dump(merged_config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ 统一配置已保存: {unified_config_path}")
    except Exception as e:
        print(f"❌ 保存统一配置失败: {e}")
        return

    # 测试配置中心加载
    print("\n🧪 测试配置加载...")
    try:
        config = config_center.load_config()
        print(f"✅ 配置加载成功，共 {len(config)} 个配置项")

        # 显示一些配置信息
        app_name = config_center.get_config("app.name", "未知应用")
        app_version = config_center.get_config("app.version", "未知版本")
        print(f"应用名称: {app_name}")
        print(f"应用版本: {app_version}")

    except Exception as e:
        print(f"❌ 测试配置加载失败: {e}")

    print("\n🎉 配置迁移完成！")
    print("\n📋 后续步骤:")
    print("1. 检查生成的统一配置文件")
    print("2. 更新代码中的配置引用")
    print("3. 测试应用功能")
    print("4. 备份原始配置文件")


if __name__ == "__main__":
    main()
