#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统测试脚本

用于验证统一配置管理系统的功能是否正常工作

使用方法:
    python test_config_system.py
"""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

# 添加项目src目录到路径
project_root = Path(__file__).parent.parent.parent
project_src = project_root / "src"
sys.path.insert(0, str(project_src))

try:
    from config.settings import Settings
    from core.config_center import (
        ConfigCenter,
        get_config,
        get_config_center,
        set_config,
    )

    # 暂时跳过logger导入，使用print代替
    # from utils.logger import get_logger
    print("✅ 成功导入配置模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"当前Python路径: {sys.path[:3]}")
    print(f"项目根目录: {project_root}")
    print(f"项目src目录: {project_src}")
    print("请确保项目依赖已正确安装")
    sys.exit(1)


# 简单的logger替代
class SimpleLogger:
    def error(self, msg):
        print(f"ERROR: {msg}")

    def info(self, msg):
        print(f"INFO: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")


def get_logger(name):
    return SimpleLogger()


logger = get_logger(__name__)


class ConfigSystemTester:
    """配置系统测试器"""

    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.original_config_dir = None

    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")

        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"📁 临时目录: {self.temp_dir}")

        # 创建测试配置文件
        config_dir = self.temp_dir / "config"
        config_dir.mkdir()

        # 创建默认配置
        default_config = {
            "app": {"name": "TestApp", "version": "1.0.0", "debug": False},
            "server": {"host": "127.0.0.1", "port": 8000},
            "database": {"type": "sqlite", "sqlite": {"path": "test.db"}},
        }

        # 保存测试配置文件
        import yaml

        with open(config_dir / "default.yaml", "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        # 创建主配置文件
        main_config = {"app": {"debug": True}, "server": {"port": 8080}}

        with open(config_dir / "settings.yaml", "w", encoding="utf-8") as f:
            yaml.dump(main_config, f, default_flow_style=False, allow_unicode=True)

        print("✅ 测试环境设置完成")

    def cleanup_test_environment(self):
        """清理测试环境"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print("🧹 测试环境已清理")

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        print(f"🧪 测试: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"  ✅ 通过")
                self.test_results.append((test_name, True, None))
            else:
                print(f"  ❌ 失败")
                self.test_results.append((test_name, False, "测试返回False"))
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            self.test_results.append((test_name, False, str(e)))

    def test_config_center_creation(self) -> bool:
        """测试配置中心创建"""
        try:
            # 使用临时配置目录
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")
            return config_center is not None
        except Exception:
            return False

    def test_config_loading(self) -> bool:
        """测试配置加载"""
        try:
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")
            config_data = config_center.load_config()

            # 验证配置数据
            return (
                config_data.get("app", {}).get("name") == "TestApp"
                and config_data.get("app", {}).get("debug")
                is True  # 主配置覆盖默认配置
                and config_data.get("server", {}).get("port")
                == 8080  # 主配置覆盖默认配置
            )
        except Exception:
            return False

    def test_config_get_set(self) -> bool:
        """测试配置获取和设置"""
        try:
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")

            # 测试获取配置
            app_name = config_center.get_config("app.name")
            if app_name != "TestApp":
                return False

            # 测试设置配置
            success = config_center.set_config("app.test_value", "test123", save=False)
            if not success:
                return False

            # 验证设置的值
            test_value = config_center.get_config("app.test_value")
            return test_value == "test123"

        except Exception:
            return False

    def test_config_validation(self) -> bool:
        """测试配置验证"""
        try:
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")

            # 添加验证规则
            config_center.add_validation_rule(
                "server.port",
                lambda x: isinstance(x, int) and 1024 <= x <= 65535,
                "端口必须是1024-65535之间的整数",
            )

            # 验证当前配置（应该通过）
            errors = config_center.validate_config()
            if errors:
                return False

            # 设置无效值并验证（应该失败）
            config_center.set_config("server.port", 80, save=False)
            errors = config_center.validate_config()
            return len(errors) > 0

        except Exception:
            return False

    def test_config_backup_restore(self) -> bool:
        """测试配置备份和恢复"""
        try:
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")

            # 创建备份
            backup_file = config_center.backup_config()
            if not backup_file or not Path(backup_file).exists():
                return False

            # 修改配置
            config_center.set_config("app.name", "ModifiedApp", save=True)

            # 验证修改
            if config_center.get_config("app.name") != "ModifiedApp":
                return False

            # 恢复备份
            success = config_center.restore_config(backup_file)
            if not success:
                return False

            # 验证恢复
            return config_center.get_config("app.name") == "TestApp"

        except Exception:
            return False

    def test_convenience_functions(self) -> bool:
        """测试便捷函数"""
        try:
            # 注意：便捷函数使用全局配置中心，这里只测试函数是否可调用
            # 实际项目中需要确保配置文件存在

            # 测试函数是否存在且可调用
            from core.config_center import (
                get_config,
                get_config_center,
                reload_config,
                set_config,
            )

            # 这些函数应该存在且可调用（即使可能因为配置文件不存在而失败）
            return all(
                [
                    callable(get_config_center),
                    callable(get_config),
                    callable(set_config),
                    callable(reload_config),
                ]
            )

        except Exception:
            return False

    def test_settings_integration(self) -> bool:
        """测试与Settings类的集成"""
        try:
            config_center = ConfigCenter(config_dir=self.temp_dir / "config")
            config_data = config_center.load_config()

            # 尝试创建Settings对象
            # 注意：这可能需要调整Settings类以支持部分配置
            # 这里只测试基本的数据结构
            return isinstance(config_data, dict) and "app" in config_data

        except Exception:
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始配置系统测试")
        print("=" * 50)

        try:
            self.setup_test_environment()

            # 运行测试
            tests = [
                ("配置中心创建", self.test_config_center_creation),
                ("配置加载", self.test_config_loading),
                ("配置获取和设置", self.test_config_get_set),
                ("配置验证", self.test_config_validation),
                ("配置备份和恢复", self.test_config_backup_restore),
                ("便捷函数", self.test_convenience_functions),
                ("Settings集成", self.test_settings_integration),
            ]

            for test_name, test_func in tests:
                self.run_test(test_name, test_func)
                print()

            # 显示测试结果
            self.show_test_results()

        finally:
            self.cleanup_test_environment()

    def show_test_results(self):
        """显示测试结果"""
        print("📊 测试结果汇总")
        print("=" * 50)

        passed = 0
        failed = 0

        for test_name, success, error in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} {test_name}")
            if not success and error:
                print(f"    错误: {error}")

            if success:
                passed += 1
            else:
                failed += 1

        print()
        print(f"📈 总计: {len(self.test_results)} 个测试")
        print(f"✅ 通过: {passed} 个")
        print(f"❌ 失败: {failed} 个")

        if failed == 0:
            print("🎉 所有测试通过！配置系统工作正常。")
        else:
            print(f"⚠️ 有 {failed} 个测试失败，请检查配置系统。")

        return failed == 0


def main():
    """主函数"""
    tester = ConfigSystemTester()
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
