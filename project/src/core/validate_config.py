#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统验证脚本

验证统一配置管理系统的功能和完整性
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

# 添加项目src目录到路径
project_root = Path(__file__).parent.parent.parent
project_src = project_root / "src"
sys.path.insert(0, str(project_src))

try:
    from core.config_center import (
        ConfigCenter,
        get_config,
    )

    print("✅ 成功导入配置模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


class ConfigValidator:
    """配置验证器"""

    def __init__(self):
        self.config_center = ConfigCenter(project_root)
        self.validation_results = []
        self.errors = []
        self.warnings = []

    def validate_all(self) -> Dict[str, Any]:
        """执行所有验证"""
        print("=== 配置系统验证 ===")

        # 基础功能验证
        self.validate_basic_functionality()

        # 配置完整性验证
        self.validate_config_completeness()

        # 配置一致性验证
        self.validate_config_consistency()

        # 环境变量验证
        self.validate_environment_variables()

        # 路径验证
        self.validate_paths()

        # 生成验证报告
        return self.generate_report()

    def validate_basic_functionality(self):
        """验证基础功能"""
        print("\n🔧 验证基础功能...")

        try:
            # 测试配置加载
            config = self.config_center.load_config()
            self.add_result("配置加载", True, f"成功加载 {len(config)} 个配置项")

            # 测试配置获取
            app_name = self.config_center.get_config("app.name")
            if app_name:
                self.add_result("配置获取", True, f"应用名称: {app_name}")
            else:
                self.add_result("配置获取", False, "无法获取应用名称")

            # 测试配置设置
            test_key = "test.validation"
            test_value = "验证测试值"
            success = self.config_center.set_config(
                test_key, test_value, save_to_user=False
            )
            if success:
                retrieved_value = self.config_center.get_config(test_key)
                if retrieved_value == test_value:
                    self.add_result("配置设置", True, "配置设置和获取正常")
                else:
                    self.add_result("配置设置", False, "配置设置后无法正确获取")
            else:
                self.add_result("配置设置", False, "配置设置失败")

            # 测试便捷函数
            convenience_value = get_config("app.version", "1.0.0")
            self.add_result("便捷函数", True, f"版本: {convenience_value}")

        except Exception as e:
            self.add_error(f"基础功能验证失败: {e}")

    def validate_config_completeness(self):
        """验证配置完整性"""
        print("\n📋 验证配置完整性...")

        required_sections = [
            "app",
            "server",
            "ai",
            "creo",
            "database",
            "storage",
            "logging",
            "security",
            "performance",
        ]

        config = self.config_center.load_config()

        for section in required_sections:
            if section in config:
                self.add_result(f"配置节 {section}", True, "存在")
            else:
                self.add_warning(f"缺少配置节: {section}")

        # 检查关键配置项
        critical_configs = ["app.name", "app.version", "server.host", "server.port"]

        for config_key in critical_configs:
            value = self.config_center.get_config(config_key)
            if value is not None:
                self.add_result(f"关键配置 {config_key}", True, str(value))
            else:
                self.add_warning(f"缺少关键配置: {config_key}")

    def validate_config_consistency(self):
        """验证配置一致性"""
        print("\n🔍 验证配置一致性...")

        try:
            # 验证配置的内部一致性
            # 检查关键配置是否存在且有效
            key_configs = ["app.name", "app.version", "server.host", "server.port"]

            for config_key in key_configs:
                config_value = self.config_center.get_config(config_key)
                if config_value is not None:
                    self.add_result(f"一致性 {config_key}", True, f"值: {config_value}")
                else:
                    self.add_warning(f"配置缺失: {config_key}")

        except Exception as e:
            self.add_error(f"配置一致性验证失败: {e}")

    def validate_environment_variables(self):
        """验证环境变量"""
        print("\n🌍 验证环境变量...")

        import os

        # 检查重要的环境变量
        important_env_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DATABASE_URL",
            "ENVIRONMENT",
        ]

        for env_var in important_env_vars:
            value = os.getenv(env_var)
            if value:
                # 不显示敏感信息的完整值
                if "KEY" in env_var or "PASSWORD" in env_var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "已设置"
                else:
                    display_value = value
                self.add_result(f"环境变量 {env_var}", True, display_value)
            else:
                self.add_warning(f"未设置环境变量: {env_var}")

    def validate_paths(self):
        """验证路径配置"""
        print("\n📁 验证路径配置...")

        # 检查重要路径
        paths_to_check = [
            ("config", "配置目录"),
            ("logs", "日志目录"),
            ("data", "数据目录"),
            ("temp", "临时目录"),
        ]

        for path_name, description in paths_to_check:
            path = project_root / path_name
            if path.exists():
                self.add_result(f"路径 {description}", True, str(path))
            else:
                self.add_warning(f"路径不存在: {description} ({path})")

        # 检查配置文件
        config_files = [
            ("config/settings.yaml", "主配置文件"),
            ("config/unified_settings.yaml", "统一配置文件"),
        ]

        for file_path, description in config_files:
            full_path = project_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.add_result(f"文件 {description}", True, f"{size} bytes")
            else:
                self.add_warning(f"文件不存在: {description} ({full_path})")

    def add_result(self, test_name: str, success: bool, message: str):
        """添加验证结果"""
        result = {"test": test_name, "success": success, "message": message}
        self.validation_results.append(result)

        status = "✅" if success else "❌"
        print(f"  {status} {test_name}: {message}")

    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
        print(f"  ❌ 错误: {message}")

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
        print(f"  ⚠️ 警告: {message}")

    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        print("\n📊 生成验证报告...")

        total_tests = len(self.validation_results)
        successful_tests = sum(1 for r in self.validation_results if r["success"])
        failed_tests = total_tests - successful_tests

        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "warnings": len(self.warnings),
                "errors": len(self.errors),
                "success_rate": (
                    f"{(successful_tests/total_tests*100):.1f}%"
                    if total_tests > 0
                    else "0%"
                ),
            },
            "results": self.validation_results,
            "warnings": self.warnings,
            "errors": self.errors,
        }

        # 保存报告
        report_path = project_root / "config" / "validation_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ 验证报告已保存: {report_path}")
        except Exception as e:
            print(f"❌ 保存验证报告失败: {e}")

        return report


def main():
    """主函数"""
    validator = ConfigValidator()
    report = validator.validate_all()

    print("\n" + "=" * 50)
    print("📋 验证总结")
    print("=" * 50)
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"成功测试: {report['summary']['successful_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"警告数量: {report['summary']['warnings']}")
    print(f"错误数量: {report['summary']['errors']}")
    print(f"成功率: {report['summary']['success_rate']}")

    if report["summary"]["failed_tests"] == 0 and report["summary"]["errors"] == 0:
        print("\n🎉 配置系统验证通过！")
        return 0
    else:
        print("\n⚠️ 配置系统存在问题，请检查报告详情")
        return 1


if __name__ == "__main__":
    sys.exit(main())
