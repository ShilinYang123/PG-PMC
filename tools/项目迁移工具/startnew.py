#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3AI项目模板迁移工具

功能：
1. 自动检测新项目根目录
2. 清理模板中的运行时数据
3. 更新项目配置文件
4. 重置文档模板
5. 初始化新项目环境

使用方法：
    # 在新项目根目录下运行（自动使用目录名称作为项目名称）
    python tools/项目迁移工具/startnew.py

    # 详细输出
    python tools/项目迁移工具/startnew.py --verbose

作者：雨俊
版本：1.0
更新：2025-01-20
"""

# import os  # 未使用的导入
import sys
import shutil
import argparse
import logging
import yaml
import json
import re
from pathlib import Path
from datetime import datetime
# from typing import Dict, List, Optional  # 未使用的导入

# 添加tools目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入项目工具
try:
    from exceptions import ValidationError, ErrorHandler
    from utils import ensure_dir_exists
    from config_loader import ConfigLoader
except ImportError:
    print("警告: 无法导入项目工具模块，使用基础功能")

    class ValidationError(Exception):
        pass

    class ErrorHandler:
        def handle_error(self, error, context=""):
            logging.error(f"{context}: {error}")

    def ensure_dir_exists(path):
        Path(path).mkdir(parents=True, exist_ok=True)
        return True

    class ConfigLoader:
        def __init__(self, project_root):
            self.project_root = project_root

        def _process_template_variables(self, content, project_name=None):
            if isinstance(content, str):
                content = content.replace(
                    '{{PROJECT_NAME}}', project_name or 'NewProject')
                content = content.replace(
                    '{{PROJECT_ROOT}}', str(
                        self.project_root))
                content = content.replace(
                    '{{PROJECT_DESCRIPTION}}', f'{project_name}项目')
                content = content.replace(
                    '{{CREATED_AT}}', datetime.now().isoformat())
                content = content.replace(
                    '{{UPDATED_AT}}', datetime.now().isoformat())
            return content

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/其他日志/项目迁移.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
error_handler = ErrorHandler()


class ProjectMigrator:
    """项目迁移处理器"""

    def __init__(
            self,
            project_root: Path,
            project_name: str = None,
            verbose: bool = False):
        self.project_root = project_root
        self.project_name = project_name or project_root.name
        self.verbose = verbose
        self.backup_dir = project_root / "bak" / "迁移备份"

        # 确保日志目录存在
        ensure_dir_exists(project_root / "logs")

        logger.info(f"初始化项目迁移器: {self.project_root}")
        logger.info(f"项目名称: {self.project_name}")

    def run_migration(self) -> bool:
        """执行完整的项目迁移流程"""
        try:
            logger.info("=" * 60)
            logger.info("开始项目迁移流程")
            logger.info("=" * 60)

            # 1. 验证项目结构
            if not self._validate_project_structure():
                return False

            # 2. 创建备份
            self._create_backup()

            # 3. 清理运行时数据
            self._clean_runtime_data()

            # 4. 更新配置文件
            self._update_configurations()

            # 5. 重置文档模板
            self._reset_document_templates()

            # 6. 更新工具脚本
            self._update_tool_scripts()

            # 7. 处理测试文件
            self._update_test_files()

            # 8. 清理缓存文件
            self._clean_cache_files()

            # 9. 验证迁移结果
            self._validate_migration()

            # 10. 生成迁移报告
            self._generate_migration_report()

            logger.info("=" * 60)
            logger.info("项目迁移完成！")
            logger.info(f"新项目名称: {self.project_name}")
            logger.info(f"项目根目录: {self.project_root}")
            logger.info("=" * 60)

            return True

        except Exception as e:
            error_handler.handle_error(e, "项目迁移失败")
            return False

    def _validate_project_structure(self) -> bool:
        """验证项目结构完整性"""
        logger.info("验证项目结构...")

        required_dirs = ['bak', 'docs', 'logs', 'project', 'tools']
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            logger.error(f"缺少必需目录: {missing_dirs}")
            return False

        logger.info("项目结构验证通过")
        return True

    def _create_backup(self):
        """创建迁移前备份"""
        logger.info("创建迁移备份...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"迁移前备份_{timestamp}"
        backup_path = self.backup_dir / backup_name

        ensure_dir_exists(backup_path)

        # 备份关键配置文件
        config_files = [
            "docs/03-管理/project_config.yaml",
            "docs/03-管理/.env",
            "docs/02-开发/memory.json",
            "docs/02-开发/tasks.json"
        ]

        for config_file in config_files:
            source = self.project_root / config_file
            if source.exists():
                target = backup_path / config_file
                ensure_dir_exists(target.parent)
                shutil.copy2(source, target)
                logger.info(f"备份: {config_file}")

    def _clean_runtime_data(self):
        """清理运行时数据"""
        logger.info("清理运行时数据...")

        # 清理日志文件
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                log_file.unlink()
                logger.info(f"删除日志: {log_file.name}")

            for json_file in logs_dir.glob("*.json"):
                json_file.unlink()
                logger.info(f"删除日志: {json_file.name}")

            for txt_file in logs_dir.glob("*.txt"):
                txt_file.unlink()
                logger.info(f"删除日志: {txt_file.name}")

        # 清理开发数据
        dev_files = [
            "docs/02-开发/memory.json",
            "docs/02-开发/tasks.json"
        ]

        for dev_file in dev_files:
            file_path = self.project_root / dev_file
            if file_path.exists():
                file_path.unlink()
                logger.info(f"删除开发数据: {dev_file}")

        # 清理历史备份（保留备份目录结构）
        bak_dirs = ['专项备份', '日常备份', '待清理资料']
        for bak_dir in bak_dirs:
            bak_path = self.project_root / "bak" / bak_dir
            if bak_path.exists():
                for item in bak_path.iterdir():
                    if item.is_file():
                        item.unlink()
                        logger.info(f"清理备份文件: {item.name}")

    def _update_configurations(self):
        """更新配置文件"""
        logger.info("更新项目配置...")

        # 初始化配置加载器
        try:
            config_loader = ConfigLoader(self.project_root)
        except BaseException:
            config_loader = None

        # 更新project_config.yaml
        config_file = self.project_root / "docs/03-管理/project_config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 处理模板变量
            if config_loader:
                content = config_loader._process_template_variables(
                    content, self.project_name)
            else:
                content = content.replace(
                    '{{PROJECT_NAME}}', self.project_name)
                content = content.replace(
                    '{{PROJECT_ROOT}}', str(
                        self.project_root))
                content = content.replace(
                    '{{PROJECT_DESCRIPTION}}', f'{
                        self.project_name}项目')
                content = content.replace(
                    '{{CREATED_AT}}', datetime.now().isoformat())
                content = content.replace(
                    '{{UPDATED_AT}}', datetime.now().isoformat())

            # 解析并更新配置
            config = yaml.safe_load(content)

            # 确保项目信息正确
            if 'project' not in config:
                config['project'] = {}
            config['project']['name'] = self.project_name
            config['project']['root'] = str(self.project_root)
            config['project']['created_at'] = datetime.now().isoformat()
            config['project']['updated_at'] = datetime.now().isoformat()

            # 更新数据库配置
            if 'database' in config:
                if 'name' in config['database']:
                    config['database']['name'] = f"{
                        self.project_name.lower().replace(
                            '-', '_')}_db"

            # 更新应用配置
            if 'app' in config:
                if 'name' in config['app']:
                    config['app']['name'] = self.project_name

            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True)

            logger.info("更新project_config.yaml完成")

        # 更新package.json（如果存在）
        package_file = self.project_root / "package.json"
        if package_file.exists():
            with open(package_file, 'r', encoding='utf-8') as f:
                package_config = json.load(f)

            package_config['name'] = self.project_name.lower().replace(
                ' ', '-')
            package_config['description'] = f'{self.project_name}项目'

            with open(package_file, 'w', encoding='utf-8') as f:
                json.dump(package_config, f, indent=2, ensure_ascii=False)

            logger.info("更新package.json完成")

        # 重置.env文件
        env_file = self.project_root / "docs/03-管理/.env"
        if env_file.exists():
            env_example = self.project_root / "docs/03-管理/.env.example"
            if env_example.exists():
                shutil.copy2(env_example, env_file)

                # 更新.env文件中的项目名称
                content = env_file.read_text(encoding='utf-8')
                content = content.replace(
                    '{{PROJECT_NAME}}', self.project_name)
                content = content.replace(
                    '{{PROJECT_ROOT}}', str(
                        self.project_root))
                env_file.write_text(content, encoding='utf-8')

                logger.info("重置并更新.env文件")

        # 更新Docker配置（如果存在）
        self._update_docker_configs()

        # 更新其他配置文件
        self._update_other_configs()

    def _update_docker_configs(self):
        """更新Docker配置文件"""
        logger.info("更新Docker配置...")

        # 更新docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            content = compose_file.read_text(encoding='utf-8')
            content = content.replace(
                '{{PROJECT_NAME}}',
                self.project_name.lower().replace(
                    ' ',
                    '-'))
            content = content.replace(
                '{{PROJECT_ROOT}}', str(
                    self.project_root))
            compose_file.write_text(content, encoding='utf-8')
            logger.info("更新docker-compose.yml")

        # 更新Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text(encoding='utf-8')
            content = content.replace('{{PROJECT_NAME}}', self.project_name)
            dockerfile.write_text(content, encoding='utf-8')
            logger.info("更新Dockerfile")

    def _update_other_configs(self):
        """更新其他配置文件"""
        logger.info("更新其他配置文件...")

        # 更新README.md
        readme_files = [
            self.project_root / "README.md",
            self.project_root / "project" / "README.md"
        ]

        for readme_file in readme_files:
            if readme_file.exists():
                content = readme_file.read_text(encoding='utf-8')
                content = content.replace(
                    '{{PROJECT_NAME}}', self.project_name)
                content = content.replace(
                    '{{PROJECT_ROOT}}', str(
                        self.project_root))
                content = content.replace(
                    '{{PROJECT_DESCRIPTION}}', f'{
                        self.project_name}项目')
                readme_file.write_text(content, encoding='utf-8')
                logger.info(f"更新{readme_file.name}")

    def _reset_document_templates(self):
        """重置文档模板"""
        logger.info("重置文档模板...")

        # 处理所有文档文件
        doc_files = [
            "docs/01-设计/开发任务书.md",
            "docs/01-设计/技术路线.md",
            "docs/01-设计/项目架构设计.md",
            "docs/01-设计/目录结构标准清单.md",
            "docs/03-管理/规范与流程.md",
            "docs/03-管理/项目模板化标准.md"
        ]

        for doc_file in doc_files:
            file_path = self.project_root / doc_file
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')

                # 替换模板变量
                content = content.replace(
                    '{{PROJECT_NAME}}', self.project_name)
                content = content.replace(
                    '{{PROJECT_ROOT}}', str(
                        self.project_root))
                content = content.replace(
                    '{{PROJECT_DESCRIPTION}}', f'{
                        self.project_name}项目')
                content = content.replace(
                    '{{CREATED_AT}}', datetime.now().isoformat())
                content = content.replace(
                    '{{UPDATED_AT}}', datetime.now().isoformat())

                # 特殊处理：更新标题
                if "开发任务书" in doc_file:
                    content = re.sub(
                        r'项目名称：.*',
                        f'项目名称：{
                            self.project_name}',
                        content)
                    content = re.sub(
                        r'# .*项目开发任务书',
                        f'# {
                            self.project_name}项目开发任务书',
                        content)
                elif "技术路线" in doc_file:
                    content = re.sub(
                        r'# .*技术路线',
                        f'# {
                            self.project_name}技术路线',
                        content)
                elif "项目架构设计" in doc_file:
                    content = re.sub(
                        r'# .*项目架构设计',
                        f'# {
                            self.project_name}项目架构设计',
                        content)

                file_path.write_text(content, encoding='utf-8')
                logger.info(f"更新{doc_file}")

    def _clean_cache_files(self):
        """清理缓存文件"""
        logger.info("清理缓存文件...")

        # 清理Python缓存
        pycache_dirs = list(self.project_root.rglob("__pycache__"))
        for pycache_dir in pycache_dirs:
            shutil.rmtree(pycache_dir)
            logger.info(f"删除缓存目录: {pycache_dir}")

        # 清理.pyc文件
        pyc_files = list(self.project_root.rglob("*.pyc"))
        for pyc_file in pyc_files:
            pyc_file.unlink()
            logger.info(f"删除缓存文件: {pyc_file}")

        # 清理临时文件
        temp_patterns = ['*.tmp', '*.temp', '*.bak', '*.swp', '*~']
        for pattern in temp_patterns:
            temp_files = list(self.project_root.rglob(pattern))
            for temp_file in temp_files:
                temp_file.unlink()
                logger.info(f"删除临时文件: {temp_file}")

    def _update_tool_scripts(self):
        """更新工具脚本"""
        logger.info("更新工具脚本...")

        # 更新工具目录下的Python脚本
        tools_dir = self.project_root / "tools"
        if tools_dir.exists():
            for py_file in tools_dir.rglob("*.py"):
                if py_file.name == "startnew.py":  # 跳过当前脚本
                    continue

                try:
                    content = py_file.read_text(encoding='utf-8')
                    original_content = content

                    # 替换模板变量
                    content = content.replace(
                        '{{PROJECT_NAME}}', self.project_name)
                    content = content.replace(
                        '{{PROJECT_ROOT}}', str(
                            self.project_root))
                    content = content.replace(
                        '{{PROJECT_DESCRIPTION}}', f'{
                            self.project_name}项目')

                    # 更新硬编码的项目名称引用
                    content = re.sub(
                        r'3AI(?!项目迁移工具)', self.project_name, content)
                    content = re.sub(
                        r'3ai(?!项目迁移工具)', self.project_name.lower(), content)

                    if content != original_content:
                        py_file.write_text(content, encoding='utf-8')
                        logger.info(
                            f"更新工具脚本: {
                                py_file.relative_to(
                                    self.project_root)}")

                except Exception as e:
                    logger.warning(f"更新工具脚本失败 {py_file}: {e}")

    def _update_test_files(self):
        """更新测试文件"""
        logger.info("更新测试文件...")

        # 更新测试目录下的文件
        test_dirs = [
            self.project_root / "tools" / "tests",
            self.project_root / "project" / "tests",
            self.project_root / "tests"
        ]

        for test_dir in test_dirs:
            if test_dir.exists():
                for test_file in test_dir.rglob("*.py"):
                    try:
                        content = test_file.read_text(encoding='utf-8')
                        original_content = content

                        # 替换模板变量
                        content = content.replace(
                            '{{PROJECT_NAME}}', self.project_name)
                        content = content.replace(
                            '{{PROJECT_ROOT}}', str(self.project_root))

                        # 更新测试路径
                        content = re.sub(
                            r's:\\3AI', str(
                                self.project_root).replace(
                                '\\', '\\\\'), content)
                        content = re.sub(
                            r'S:\\3AI', str(
                                self.project_root).replace(
                                '\\', '\\\\'), content)

                        if content != original_content:
                            test_file.write_text(content, encoding='utf-8')
                            logger.info(
                                f"更新测试文件: {
                                    test_file.relative_to(
                                        self.project_root)}")

                    except Exception as e:
                        logger.warning(f"更新测试文件失败 {test_file}: {e}")

    def _validate_migration(self):
        """验证迁移结果"""
        logger.info("验证迁移结果...")

        validation_errors = []

        # 验证配置文件
        config_file = self.project_root / "docs/03-管理/project_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # 检查是否还有未替换的模板变量
                config_str = yaml.dump(config)
                if '{{' in config_str and '}}' in config_str:
                    validation_errors.append("配置文件中仍有未替换的模板变量")

                # 检查项目名称是否正确设置
                if config.get('project', {}).get('name') != self.project_name:
                    validation_errors.append("项目名称未正确设置")

            except Exception as e:
                validation_errors.append(f"配置文件验证失败: {e}")

        # 验证关键目录存在
        required_dirs = ['docs', 'tools', 'logs', 'bak']
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                validation_errors.append(f"缺少必需目录: {dir_name}")

        # 验证工具脚本
        key_tools = [
            "tools/config_loader.py",
            "tools/项目迁移工具/startnew.py"
        ]
        for tool in key_tools:
            if not (self.project_root / tool).exists():
                validation_errors.append(f"缺少关键工具: {tool}")

        if validation_errors:
            logger.warning("迁移验证发现问题:")
            for error in validation_errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("迁移验证通过")

    def _generate_migration_report(self):
        """生成迁移报告"""
        logger.info("生成迁移报告...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.project_root / "logs" / \
            "检查报告" / f"项目迁移报告_{timestamp}.md"

        report_content = """# {self.project_name}项目迁移报告

## 基本信息

- **项目名称**: {self.project_name}
- **项目根目录**: {self.project_root}
- **迁移时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **迁移工具版本**: 1.0

## 迁移步骤

✅ 项目结构验证
✅ 创建迁移备份
✅ 清理运行时数据
✅ 更新配置文件
✅ 重置文档模板
✅ 更新工具脚本
✅ 处理测试文件
✅ 清理缓存文件
✅ 验证迁移结果
✅ 生成迁移报告

## 清理内容

### 运行时数据
- 删除logs目录下的所有日志文件
- 删除docs/02-开发/memory.json
- 删除docs/02-开发/tasks.json
- 清理bak目录下的历史备份文件

### 缓存文件
- 删除所有__pycache__目录
- 删除所有.pyc文件

### 配置更新
- 更新project_config.yaml中的项目信息和模板变量
- 更新package.json中的项目名称和描述
- 重置并更新.env文件
- 更新Docker配置文件（如果存在）
- 更新README.md文件

### 文档更新
- 更新所有设计文档中的项目名称和模板变量
- 更新管理文档中的项目信息
- 处理文档中的路径引用

### 工具和测试更新
- 更新所有工具脚本中的项目引用
- 更新测试文件中的路径和项目名称
- 替换硬编码的项目名称引用

## 下一步操作建议

1. 检查并完善开发任务书
2. 制定具体的技术路线
3. 配置项目特定的环境变量
4. 开始项目开发工作

## 备份位置

迁移前的重要配置文件已备份到: `bak/迁移备份/`

---

*此报告由{{PROJECT_NAME}}项目迁移工具自动生成*
"""

        report_file.write_text(report_content, encoding='utf-8')
        logger.info(f"迁移报告已生成: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="3AI项目模板迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python startnew.py                           # 自动使用根目录名称作为项目名称
  python startnew.py --verbose                 # 详细输出
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 获取项目根目录
    project_root = Path.cwd()

    # 验证是否在正确的目录中运行
    if not (project_root / "tools" / "项目迁移工具" / "startnew.py").exists():
        print("错误: 请在项目根目录下运行此脚本")
        print("正确的运行方式: python tools/项目迁移工具/startnew.py")
        sys.exit(1)

    # 自动使用根目录名称作为项目名称
    project_name = project_root.name
    print(f"自动检测到项目名称: {project_name}")

    # 创建迁移器并执行迁移
    migrator = ProjectMigrator(
        project_root=project_root,
        project_name=project_name,
        verbose=args.verbose
    )

    success = migrator.run_migration()

    if success:
        print("\n🎉 项目迁移成功完成！")
        print(f"新项目已准备就绪: {migrator.project_name}")
        print("\n建议下一步操作:")
        print("1. 检查并完善 docs/01-设计/开发任务书.md")
        print("2. 制定具体的 docs/01-设计/技术路线.md")
        print("3. 配置 docs/03-管理/.env 环境变量")
        print("4. 开始项目开发工作")
        sys.exit(0)
    else:
        print("\n❌ 项目迁移失败，请检查日志文件")
        sys.exit(1)


if __name__ == "__main__":
    main()
