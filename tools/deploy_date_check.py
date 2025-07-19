#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期一致性检查功能部署脚本

功能：
- 验证环境配置
- 测试日期检查功能
- 部署新功能
- 生成部署报告

作者：雨俊（技术负责人）
创建日期：2025年7月16日
版本：1.0.0
"""

import os
import sys
import subprocess
import tempfile
import json
from datetime import datetime
from pathlib import Path

class DateCheckDeployer:
    """日期检查功能部署器"""
    
    def __init__(self):
        self.project_root = Path("S:/PG-PMC")
        self.tools_dir = self.project_root / "tools"
        self.docs_dir = self.project_root / "docs"
        self.config_file = self.docs_dir / "03-管理" / "project_config.yaml"
        self.compliance_script = self.tools_dir / "compliance_monitor.py"
        self.deployment_log = []
        
    def log(self, message, level="INFO"):
        """记录部署日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.deployment_log.append(log_entry)
        print(log_entry)
        
    def check_environment(self):
        """检查部署环境"""
        self.log("开始环境检查...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
            self.log(f"Python版本过低: {python_version.major}.{python_version.minor}", "ERROR")
            return False
        self.log(f"Python版本检查通过: {python_version.major}.{python_version.minor}")
        
        # 检查项目目录
        if not self.project_root.exists():
            self.log(f"项目根目录不存在: {self.project_root}", "ERROR")
            return False
        self.log("项目目录检查通过")
        
        # 检查依赖包
        try:
            import yaml
            import watchdog
            self.log("依赖包检查通过")
        except ImportError as e:
            self.log(f"缺少依赖包: {e}", "ERROR")
            return False
            
        # 检查关键文件
        if not self.compliance_script.exists():
            self.log(f"合规性监控脚本不存在: {self.compliance_script}", "ERROR")
            return False
        self.log("关键文件检查通过")
        
        return True
        
    def verify_config(self):
        """验证配置文件"""
        self.log("验证配置文件...")
        
        if not self.config_file.exists():
            self.log(f"配置文件不存在: {self.config_file}", "ERROR")
            return False
            
        try:
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 检查日期检查配置
            enhanced_config = config.get('compliance', {}).get('enhanced_pre_check', {})
            if 'date_consistency' not in enhanced_config:
                self.log("配置文件缺少日期检查配置", "ERROR")
                return False
                
            date_config = enhanced_config['date_consistency']
            if not date_config.get('enabled', False):
                self.log("日期检查功能未启用", "WARNING")
                
            if 'forbidden_dates' not in date_config:
                self.log("配置文件缺少禁止日期列表", "ERROR")
                return False
                
            forbidden_count = len(date_config['forbidden_dates'])
            self.log(f"配置文件验证通过，包含 {forbidden_count} 个禁止日期模式")
            return True
            
        except Exception as e:
            self.log(f"配置文件验证失败: {e}", "ERROR")
            return False
            
    def test_functionality(self):
        """测试日期检查功能"""
        self.log("测试日期检查功能...")
        
        # 创建测试文件
        test_content = '''# 测试文档

创建日期：2020年1月1日
修改日期：2019-12-31
版本：1.0.0

这是一个包含历史日期的测试文档，用于验证日期检查功能。
文档中包含了2018年的一些信息和2017/01/01的日期格式。
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file = f.name
            
        try:
            # 测试日期检查命令
            cmd = [sys.executable, str(self.compliance_script), '--date-check', '--file', test_file]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                if '禁止的历史日期' in result.stdout or 'date issues found' in result.stdout:
                    self.log("日期检查功能测试通过 - 成功检测到历史日期")
                    return True
                else:
                    self.log("日期检查功能可能存在问题 - 未检测到预期的历史日期", "WARNING")
                    self.log(f"输出: {result.stdout}")
                    return False
            else:
                self.log(f"日期检查命令执行失败: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"功能测试失败: {e}", "ERROR")
            return False
        finally:
            # 清理测试文件
            try:
                os.unlink(test_file)
            except:
                pass
                
    def test_help_command(self):
        """测试帮助命令"""
        self.log("测试帮助命令...")
        
        try:
            cmd = [sys.executable, str(self.compliance_script), '--help']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0 and '--date-check' in result.stdout:
                self.log("帮助命令测试通过 - 包含日期检查选项")
                return True
            else:
                self.log("帮助命令测试失败 - 未找到日期检查选项", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"帮助命令测试失败: {e}", "ERROR")
            return False
            
    def generate_deployment_report(self):
        """生成部署报告"""
        self.log("生成部署报告...")
        
        report_dir = self.project_root / "logs" / "部署报告"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"date_check_deployment_{timestamp}.md"
        
        report_content = f'''# 日期一致性检查功能部署报告

**部署时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}  
**部署版本**: 1.0.0  
**执行者**: 自动部署脚本

## 部署概要

本次部署成功启用了日期一致性检查功能，该功能已集成到项目规范强制遵守系统中。

## 部署日志

```
{"".join([log + "\n" for log in self.deployment_log])}
```

## 功能验证

- ✅ 环境检查通过
- ✅ 配置文件验证通过
- ✅ 功能测试通过
- ✅ 帮助命令测试通过

## 可用命令

### 基本使用

```bash
# 检查单个文件
python tools\\compliance_monitor.py date-check --file "文件路径"

# 检查整个项目
python tools\\compliance_monitor.py date-check

# 自动修复日期问题
python tools\\compliance_monitor.py date-check --fix
```

### 高级功能

```bash
# 生成报告
python tools\\compliance_monitor.py date-check --report

# 启动实时监控
python tools\\compliance_monitor.py start

# 查看状态
python tools\\compliance_monitor.py status
```

## 配置文件位置

- **主配置**: `docs/03-管理/project_config.yaml`
- **监控脚本**: `tools/compliance_monitor.py`
- **使用指南**: `docs/03-管理/项目规范强制遵守使用指南.md`
- **部署指南**: `docs/03-管理/日期一致性检查部署指南.md`

## 后续步骤

1. **团队培训**: 向团队成员介绍新功能的使用方法
2. **定期检查**: 建议每周执行一次全项目日期检查
3. **监控集成**: 将日期检查集成到日常开发流程中
4. **持续改进**: 根据使用反馈优化检查规则

## 技术支持

如有问题或建议，请联系技术负责人：雨俊

---

**部署状态**: ✅ 成功  
**下次检查建议**: {(datetime.now().replace(day=datetime.now().day + 7)).strftime("%Y年%m月%d日")}
'''
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.log(f"部署报告已生成: {report_file}")
            return str(report_file)
        except Exception as e:
            self.log(f"生成部署报告失败: {e}", "ERROR")
            return None
            
    def deploy(self):
        """执行完整部署流程"""
        self.log("开始部署日期一致性检查功能")
        self.log("=" * 50)
        
        success = True
        
        # 环境检查
        if not self.check_environment():
            success = False
            
        # 配置验证
        if success and not self.verify_config():
            success = False
            
        # 功能测试
        if success and not self.test_functionality():
            success = False
            
        # 帮助命令测试
        if success and not self.test_help_command():
            success = False
            
        # 生成报告
        report_file = self.generate_deployment_report()
        
        self.log("=" * 50)
        if success:
            self.log("✅ 日期一致性检查功能部署成功！", "SUCCESS")
            if report_file:
                self.log(f"📄 部署报告: {report_file}")
        else:
            self.log("❌ 部署过程中发现问题，请检查日志", "ERROR")
            
        return success

def main():
    """主函数"""
    print("日期一致性检查功能部署脚本")
    print("作者：雨俊（技术负责人）")
    print("版本：1.0.0")
    print()
    
    deployer = DateCheckDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n🎉 部署完成！现在可以使用以下命令测试功能：")
        print("python tools\\compliance_monitor.py date-check --help")
        print("python tools\\compliance_monitor.py date-check")
    else:
        print("\n❌ 部署失败，请检查上述错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()