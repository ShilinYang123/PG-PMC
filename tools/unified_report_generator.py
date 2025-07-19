#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一报告生成器
合并了report_generator.py和auto_report_generator.py的功能
提供统一的报告生成功能，支持多种格式输出和自动化报告生成
"""

import os
import sys
import json
import yaml
import schedule
import time
from pathlib import Path
from typing import Set, List, Optional, Dict
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from tools.config_loader import ConfigLoader
except ImportError:
    # 如果无法导入，使用默认配置
    class ConfigLoader:
        @staticmethod
        def load_config():
            return {}

try:
    from tools.compliance_monitor import ComplianceMonitor
    from tools.pre_operation_check import ProjectComplianceChecker
except ImportError:
    ComplianceMonitor = None
    ProjectComplianceChecker = None


class UnifiedReportGenerator:
    """统一报告生成器类"""

    def __init__(self, project_root_path: str = "s:/PG-PMC"):
        """初始化统一报告生成器"""
        self.project_root = Path(project_root_path)
        self.config = ConfigLoader.load_config()
        
        # 报告输出目录
        self.reports_dir = self.project_root / "logs" / "compliance_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化监控和检查器（如果可用）
        if ComplianceMonitor:
            self.monitor = ComplianceMonitor(str(self.project_root))
        else:
            self.monitor = None
            
        if ProjectComplianceChecker:
            self.checker = ProjectComplianceChecker(str(self.project_root))
        else:
            self.checker = None

    # ==================== 基础报告生成功能 ====================
    
    def generate_directory_tree(self, paths: Set[str], max_depth: int = 3) -> str:
        """生成目录树结构"""
        if not paths:
            return "(空目录)"

        # 将路径转换为Path对象并排序
        path_objects = [Path(p) for p in paths]
        path_objects.sort()

        # 构建树结构
        tree_lines = []
        processed_dirs = set()

        for path_obj in path_objects:
            # 获取相对于项目根目录的路径
            try:
                rel_path = path_obj.relative_to(self.project_root)
            except ValueError:
                rel_path = path_obj

            parts = rel_path.parts
            if len(parts) > max_depth:
                continue

            # 构建每一级的缩进
            for i, part in enumerate(parts):
                current_path = Path(*parts[: i + 1])
                if current_path not in processed_dirs:
                    indent = "│   " * i
                    if i == len(parts) - 1:
                        # 最后一级，判断是文件还是目录
                        if path_obj.is_dir():
                            tree_lines.append(f"{indent}├── {part}/")
                        else:
                            tree_lines.append(f"{indent}├── {part}")
                    else:
                        tree_lines.append(f"{indent}├── {part}/")
                    processed_dirs.add(current_path)

        return "\n".join(tree_lines)

    def format_file_list(self, files: List[Path], title: str = "文件列表") -> str:
        """格式化文件列表"""
        if not files:
            return f"## {title}\n\n(无文件)\n\n"

        content = f"## {title}\n\n"
        for file_path in sorted(files):
            try:
                rel_path = file_path.relative_to(self.project_root)
                content += f"- {rel_path}\n"
            except ValueError:
                content += f"- {file_path}\n"

        return content + "\n"

    def format_directory_list(self, directories: List[Path], title: str = "目录列表") -> str:
        """格式化目录列表"""
        if not directories:
            return f"## {title}\n\n(无目录)\n\n"

        content = f"## {title}\n\n"
        for dir_path in sorted(directories):
            try:
                rel_path = dir_path.relative_to(self.project_root)
                content += f"- {rel_path}/\n"
            except ValueError:
                content += f"- {dir_path}/\n"

        return content + "\n"

    def save_report(self, content: str, output_file: Path, message: str = "报告已保存") -> None:
        """保存报告到文件"""
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            self._print_file_link(message, output_file)

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            raise

    def _print_file_link(self, message: str, file_path: Optional[Path] = None) -> str:
        """打印可点击的文件链接"""
        if file_path:
            # 在终端中显示可点击的文件链接
            clickable_link = f"file:///{file_path.as_posix()}"
            print(f"{message}: {clickable_link}")
            return f"{message}: {clickable_link}"
        return message

    def generate_standard_report_header(self, tool_name: str, directories_count: int, 
                                      files_count: int, template_files_count: int = 0) -> str:
        """生成标准报告头部"""
        # 从配置文件读取时间戳格式
        structure_config = self.config.get("structure_check", {})
        reporting_config = structure_config.get("reporting", {})
        timestamp_format = reporting_config.get("timestamp_format", "%Y-%m-%d %H:%M:%S")

        timestamp = datetime.now().strftime(timestamp_format)

        header = (
            f"# 目录结构标准清单\n\n"
            f"> 生成时间: {timestamp}\n"
            f"> 生成工具: {tool_name}\n"
            f"> 目录数量: {directories_count}\n"
            f"> 文件数量: {files_count}\n"
        )

        if template_files_count > 0:
            header += f"> 模板文件: {template_files_count}\n"

        header += "\n\n"
        return header

    def generate_directory_section(self, paths: Set[str], title: str = "完整目录树") -> str:
        """生成目录结构部分"""
        tree_content = self.generate_directory_tree(paths)

        # 从配置文件读取目录树根节点名称
        structure_config = self.config.get("structure_check", {})
        reporting_config = structure_config.get("reporting", {})
        tree_config = reporting_config.get("tree_display", {})
        root_name = tree_config.get("root_name", "PinGao/")

        return (
            f"## 当前目录结构\n\n"
            f"```\n"
            f"{root_name}\n"
            f"{tree_content}\n"
            f"```\n\n"
        )

    # ==================== 自动化合规性报告功能 ====================
    
    def generate_daily_report(self):
        """生成每日合规性报告"""
        print(f"📊 生成每日合规性报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.monitor:
            print("❌ 合规性监控器不可用，无法生成报告")
            return
        
        # 获取监控状态
        status = self.monitor.get_status()
        
        # 生成报告内容
        report = {
            "report_type": "daily",
            "generated_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "monitoring_status": status,
            "summary": self._generate_summary(status),
            "recommendations": self._generate_recommendations(status)
        }
        
        # 保存报告
        report_file = self.reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown格式报告
        self._generate_markdown_report(report, "daily")
        
        print(f"✅ 每日报告已生成: {report_file}")
        
    def generate_weekly_report(self):
        """生成每周合规性报告"""
        print(f"📈 生成每周合规性报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 收集一周内的所有日报
        week_start = datetime.now() - timedelta(days=7)
        daily_reports = []
        
        for i in range(7):
            date = week_start + timedelta(days=i)
            report_file = self.reports_dir / f"daily_report_{date.strftime('%Y%m%d')}.json"
            if report_file.exists():
                with open(report_file, 'r', encoding='utf-8') as f:
                    daily_reports.append(json.load(f))
        
        # 生成周报
        report = {
            "report_type": "weekly",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": week_start.strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            },
            "daily_reports_count": len(daily_reports),
            "trends": self._analyze_trends(daily_reports),
            "summary": self._generate_weekly_summary(daily_reports)
        }
        
        # 保存周报
        report_file = self.reports_dir / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown格式报告
        self._generate_markdown_report(report, "weekly")
        
        print(f"✅ 每周报告已生成: {report_file}")
        
    def _generate_summary(self, status: Dict) -> Dict:
        """生成状态摘要"""
        total_violations = status.get('total_violations', 0)
        resolved_violations = status.get('resolved_violations', 0)
        unresolved_violations = status.get('unresolved_violations', 0)
        
        return {
            "total_violations": total_violations,
            "resolved_violations": resolved_violations,
            "unresolved_violations": unresolved_violations,
            "resolution_rate": resolved_violations / max(total_violations, 1) * 100,
            "compliance_score": max(0, 100 - unresolved_violations * 10)
        }
        
    def _generate_recommendations(self, status: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        unresolved = status.get('unresolved_violations', 0)
        if unresolved > 0:
            recommendations.append(f"🔧 需要解决 {unresolved} 个未解决的违规问题")
            
        if unresolved > 5:
            recommendations.append("⚠️ 违规数量较多，建议优先处理高严重性问题")
            
        if status.get('monitoring_status') != '运行中':
            recommendations.append("🔄 建议启动实时监控系统")
            
        return recommendations
        
    def _analyze_trends(self, daily_reports: List[Dict]) -> Dict:
        """分析趋势"""
        if not daily_reports:
            return {"trend": "无数据"}
            
        violations_trend = []
        for report in daily_reports:
            summary = report.get('summary', {})
            violations_trend.append(summary.get('unresolved_violations', 0))
            
        return {
            "violations_trend": violations_trend,
            "average_violations": sum(violations_trend) / len(violations_trend),
            "trend_direction": "改善" if violations_trend[-1] < violations_trend[0] else "恶化" if violations_trend[-1] > violations_trend[0] else "稳定"
        }
        
    def _generate_weekly_summary(self, daily_reports: List[Dict]) -> Dict:
        """生成周摘要"""
        if not daily_reports:
            return {"message": "本周无数据"}
            
        total_violations = sum(r.get('summary', {}).get('total_violations', 0) for r in daily_reports)
        avg_compliance_score = sum(r.get('summary', {}).get('compliance_score', 0) for r in daily_reports) / len(daily_reports)
        
        return {
            "total_violations_week": total_violations,
            "average_compliance_score": avg_compliance_score,
            "days_with_data": len(daily_reports),
            "compliance_grade": self._get_compliance_grade(avg_compliance_score)
        }
        
    def _get_compliance_grade(self, score: float) -> str:
        """获取合规等级"""
        if score >= 95:
            return "优秀 (A+)"
        elif score >= 90:
            return "良好 (A)"
        elif score >= 80:
            return "合格 (B)"
        elif score >= 70:
            return "需改进 (C)"
        else:
            return "不合格 (D)"
            
    def _generate_markdown_report(self, report: Dict, report_type: str):
        """生成Markdown格式报告"""
        timestamp = datetime.now().strftime('%Y%m%d')
        md_file = self.reports_dir / f"{report_type}_report_{timestamp}.md"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            if report_type == "daily":
                self._write_daily_markdown(f, report)
            else:
                self._write_weekly_markdown(f, report)
                
    def _write_daily_markdown(self, f, report: Dict):
        """写入每日Markdown报告"""
        f.write(f"# 每日合规性报告\n\n")
        f.write(f"**生成时间**: {report['generated_at']}\n\n")
        
        summary = report.get('summary', {})
        f.write(f"## 📊 合规性概览\n\n")
        f.write(f"- **合规评分**: {summary.get('compliance_score', 0):.1f}/100\n")
        f.write(f"- **总违规数**: {summary.get('total_violations', 0)}\n")
        f.write(f"- **已解决**: {summary.get('resolved_violations', 0)}\n")
        f.write(f"- **未解决**: {summary.get('unresolved_violations', 0)}\n")
        f.write(f"- **解决率**: {summary.get('resolution_rate', 0):.1f}%\n\n")
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            f.write(f"## 💡 改进建议\n\n")
            for rec in recommendations:
                f.write(f"- {rec}\n")
            f.write("\n")
                
    def _write_weekly_markdown(self, f, report: Dict):
        """写入每周Markdown报告"""
        f.write(f"# 每周合规性报告\n\n")
        f.write(f"**生成时间**: {report['generated_at']}\n\n")
        
        period = report.get('period', {})
        f.write(f"**报告周期**: {period.get('start')} 至 {period.get('end')}\n\n")
        
        summary = report.get('summary', {})
        f.write(f"## 📈 周度概览\n\n")
        f.write(f"- **平均合规评分**: {summary.get('average_compliance_score', 0):.1f}/100\n")
        f.write(f"- **合规等级**: {summary.get('compliance_grade', 'N/A')}\n")
        f.write(f"- **本周总违规**: {summary.get('total_violations_week', 0)}\n")
        f.write(f"- **有数据天数**: {summary.get('days_with_data', 0)}/7\n\n")
        
        trends = report.get('trends', {})
        f.write(f"## 📊 趋势分析\n\n")
        f.write(f"- **趋势方向**: {trends.get('trend_direction', 'N/A')}\n")
        f.write(f"- **平均违规数**: {trends.get('average_violations', 0):.1f}\n\n")

    # ==================== 定时任务功能 ====================
    
    def setup_scheduled_reports(self):
        """设置定时报告任务"""
        # 每日报告 - 每天晚上23:00生成
        schedule.every().day.at("23:00").do(self.generate_daily_report)
        
        # 每周报告 - 每周日晚上23:30生成
        schedule.every().sunday.at("23:30").do(self.generate_weekly_report)
        
        print("📅 定时报告任务已设置:")
        print("   - 每日报告: 每天 23:00")
        print("   - 每周报告: 每周日 23:30")
        
    def run_scheduler(self):
        """运行定时任务调度器"""
        print("🕐 启动报告定时任务调度器...")
        self.setup_scheduled_reports()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一报告生成器")
    parser.add_argument("--daily", action="store_true", help="生成每日报告")
    parser.add_argument("--weekly", action="store_true", help="生成每周报告")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务")
    parser.add_argument("--project-root", default="s:/PG-PMC", help="项目根目录")
    
    args = parser.parse_args()
    
    generator = UnifiedReportGenerator(args.project_root)
    
    if args.daily:
        generator.generate_daily_report()
    elif args.weekly:
        generator.generate_weekly_report()
    elif args.schedule:
        generator.run_scheduler()
    else:
        print("请指定操作: --daily, --weekly, 或 --schedule")
        parser.print_help()


if __name__ == "__main__":
    main()