#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC项目开发进度看板工具
功能：动态扫描项目文件，自动更新并图形化展示项目所有功能模块的开发状态
作者：雨俊
创建时间：2025-01-20
更新时间：2025-01-20
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ProjectKanban:
    """项目看板类"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "tools" / "kanban_config.json"
        self.modules = self._load_or_create_module_status()
        self.last_update = datetime.now()
        
    def _load_or_create_module_status(self) -> Dict:
        """加载或创建模块状态信息"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    modules = config.get('modules', {})
                    print(f"📁 从配置文件加载看板数据: {self.config_file}")
            except Exception as e:
                print(f"⚠️  配置文件读取失败，使用默认配置: {e}")
                modules = self._get_default_modules()
        else:
            print("🆕 首次运行，创建默认配置")
            modules = self._get_default_modules()
        
        # 动态扫描并更新模块状态
        self._scan_and_update_modules(modules)
        
        # 保存更新后的配置
        self._save_config(modules)
        
        return modules
    
    def _get_default_modules(self) -> Dict:
        """获取默认模块配置"""
        return {
            "后端API模块": {
                "用户认证模块": {"status": "待检测", "progress": 0, "files": ["auth.py"], "last_modified": None},
                "设备管理模块": {"status": "待检测", "progress": 0, "files": ["equipment.py"], "last_modified": None},
                "质量管理模块": {"status": "待检测", "progress": 0, "files": ["quality.py"], "last_modified": None},
                "物料管理模块": {"status": "待检测", "progress": 0, "files": ["materials.py"], "last_modified": None},
                "订单管理模块": {"status": "待检测", "progress": 0, "files": ["orders.py"], "last_modified": None},
                "生产计划模块": {"status": "待检测", "progress": 0, "files": ["production_plans.py"], "last_modified": None},
                "进度跟踪模块": {"status": "待检测", "progress": 0, "files": ["progress.py"], "last_modified": None},
                "用户管理模块": {"status": "待检测", "progress": 0, "files": ["users.py"], "last_modified": None}
            },
            "前端界面模块": {
                "仪表板页面": {"status": "待检测", "progress": 0, "files": ["Dashboard/index.tsx"], "last_modified": None},
                "订单管理页面": {"status": "待检测", "progress": 0, "files": ["OrderManagement/index.tsx"], "last_modified": None},
                "生产计划页面": {"status": "待检测", "progress": 0, "files": ["ProductionPlan/index.tsx"], "last_modified": None},
                "物料管理页面": {"status": "待检测", "progress": 0, "files": ["MaterialManagement/index.tsx"], "last_modified": None},
                "进度跟踪页面": {"status": "待检测", "progress": 0, "files": ["ProgressTracking/index.tsx"], "last_modified": None},
                "图表组件库": {"status": "待检测", "progress": 0, "files": ["components/Charts/"], "last_modified": None},
                "移动端适配": {"status": "待检测", "progress": 0, "files": ["styles/mobile.css"], "last_modified": None},
                "通知组件": {"status": "待检测", "progress": 0, "files": ["components/Notification/"], "last_modified": None}
            },
            "数据模型层": {
                "订单模型": {"status": "待检测", "progress": 0, "files": ["order.py"], "last_modified": None},
                "生产计划模型": {"status": "待检测", "progress": 0, "files": ["production_plan.py"], "last_modified": None},
                "物料模型": {"status": "待检测", "progress": 0, "files": ["material.py"], "last_modified": None},
                "进度记录模型": {"status": "待检测", "progress": 0, "files": ["progress.py"], "last_modified": None},
                "用户模型": {"status": "待检测", "progress": 0, "files": ["user.py"], "last_modified": None},
                "质量记录模型": {"status": "待检测", "progress": 0, "files": ["quality.py"], "last_modified": None},
                "设备模型": {"status": "待检测", "progress": 0, "files": ["equipment.py"], "last_modified": None}
            },
            "系统集成模块": {
                "通知催办系统": {"status": "待检测", "progress": 0, "files": ["notifications/"], "last_modified": None},
                "微信集成": {"status": "待检测", "progress": 0, "files": ["integrations/wechat.py"], "last_modified": None},
                "邮件系统": {"status": "待检测", "progress": 0, "files": ["integrations/email.py"], "last_modified": None},
                "短信通知": {"status": "待检测", "progress": 0, "files": ["integrations/sms.py"], "last_modified": None},
                "文件导入导出": {"status": "待检测", "progress": 0, "files": ["utils/import_export.py"], "last_modified": None},
                "数据备份恢复": {"status": "待检测", "progress": 0, "files": ["utils/backup.py"], "last_modified": None}
            }
        }
    
    def _scan_and_update_modules(self, modules: Dict):
        """扫描项目文件并更新模块状态"""
        print("🔍 正在扫描项目文件...")
        
        backend_path = self.project_root / "project" / "backend" / "app"
        frontend_path = self.project_root / "project" / "frontend" / "src"
        
        for category, items in modules.items():
            for module_name, info in items.items():
                if info["files"]:
                    file_exists = False
                    total_lines = 0
                    total_functions = 0
                    total_classes = 0
                    latest_modified = None
                    
                    for file_name in info["files"]:
                        file_path = self._get_file_path(category, file_name, backend_path, frontend_path)
                        
                        if file_path and file_path.exists():
                            file_exists = True
                            # 获取文件修改时间
                            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if latest_modified is None or modified_time > latest_modified:
                                latest_modified = modified_time
                            
                            # 分析文件内容
                            lines, functions, classes = self._analyze_file_content(file_path)
                            total_lines += lines
                            total_functions += functions
                            total_classes += classes
                        elif file_path and file_path.is_dir():
                            # 处理目录情况
                            dir_files = list(file_path.rglob("*.*"))
                            if dir_files:
                                file_exists = True
                                for sub_file in dir_files:
                                    modified_time = datetime.fromtimestamp(sub_file.stat().st_mtime)
                                    if latest_modified is None or modified_time > latest_modified:
                                        latest_modified = modified_time
                                    
                                    lines, functions, classes = self._analyze_file_content(sub_file)
                                    total_lines += lines
                                    total_functions += functions
                                    total_classes += classes
                    
                    # 更新模块状态
                    if file_exists:
                        # 根据代码量计算进度
                        progress = min(100, max(10, (total_lines * 2 + total_functions * 10 + total_classes * 15)))
                        
                        if progress >= 80:
                            status = "完成"
                        elif progress >= 30:
                            status = "进行中"
                        else:
                            status = "开始开发"
                    else:
                        progress = 0
                        status = "待开发"
                    
                    info["progress"] = progress
                    info["status"] = status
                    info["last_modified"] = latest_modified.isoformat() if latest_modified else None
                    info["lines"] = total_lines
                    info["functions"] = total_functions
                    info["classes"] = total_classes
    
    def _get_file_path(self, category: str, file_name: str, backend_path: Path, frontend_path: Path) -> Optional[Path]:
        """获取文件的完整路径"""
        if category == "后端API模块":
            return backend_path / "api" / "endpoints" / file_name
        elif category == "前端界面模块":
            if file_name.endswith('/'):
                return frontend_path / file_name.rstrip('/')
            return frontend_path / "pages" / file_name
        elif category == "数据模型层":
            return backend_path / "models" / file_name
        elif category == "系统集成模块":
            if file_name.endswith('/'):
                return backend_path / file_name.rstrip('/')
            return backend_path / file_name
        return None
    
    def _analyze_file_content(self, file_path: Path) -> Tuple[int, int, int]:
        """分析文件内容，返回行数、函数数、类数"""
        try:
            if file_path.suffix not in ['.py', '.tsx', '.ts', '.js', '.jsx', '.css']:
                return 0, 0, 0
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('//')])
            
            if file_path.suffix == '.py':
                functions = len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
                classes = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
            elif file_path.suffix in ['.tsx', '.ts', '.js', '.jsx']:
                functions = len(re.findall(r'(function\s+\w+|const\s+\w+\s*=\s*\(|\w+\s*:\s*\()', content))
                classes = len(re.findall(r'(class\s+\w+|interface\s+\w+)', content))
            else:
                functions = 0
                classes = 0
            
            return lines, functions, classes
        except Exception:
            return 0, 0, 0
    
    def _save_config(self, modules: Dict):
        """保存配置到文件"""
        try:
            config = {
                'modules': modules,
                'last_update': self.last_update.isoformat(),
                'version': '1.0'
            }
            
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"💾 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def update_kanban(self):
        """手动更新看板数据"""
        print("🔄 手动更新看板数据...")
        self._scan_and_update_modules(self.modules)
        self._save_config(self.modules)
        self.last_update = datetime.now()
        print("✅ 看板数据更新完成")
    
    def generate_overview_chart(self):
        """生成项目总览图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('PG-PMC项目开发进度看板', fontsize=20, fontweight='bold')
        
        # 1. 模块完成度饼图
        self._draw_completion_pie(ax1)
        
        # 2. 各类别进度条图
        self._draw_category_progress(ax2)
        
        # 3. 详细模块状态热力图
        self._draw_module_heatmap(ax3)
        
        # 4. 时间线甘特图
        self._draw_timeline_gantt(ax4)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)
        
        # 保存图表
        output_path = self.project_root / "docs" / "03-管理" / "项目进度看板.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"看板图表已保存到: {output_path}")
        
        plt.show()
    
    def _draw_completion_pie(self, ax):
        """绘制完成度饼图"""
        status_counts = {"完成": 0, "进行中": 0, "待开发": 0, "待完善": 0}
        
        for category, items in self.modules.items():
            for module_name, info in items.items():
                status_counts[info["status"]] += 1
        
        labels = list(status_counts.keys())
        sizes = list(status_counts.values())
        colors = ['#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90)
        ax.set_title('模块完成状态分布', fontsize=14, fontweight='bold')
        
        # 添加图例
        ax.legend(wedges, [f'{label}: {size}个' for label, size in zip(labels, sizes)],
                 loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    def _draw_category_progress(self, ax):
        """绘制各类别进度条"""
        categories = list(self.modules.keys())
        progress_data = []
        
        for category, items in self.modules.items():
            total_progress = sum(info["progress"] for info in items.values())
            avg_progress = total_progress / len(items) if items else 0
            progress_data.append(avg_progress)
        
        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, progress_data, color=['#3498db', '#e67e22', '#27ae60', '#8e44ad'])
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel('完成度 (%)')
        ax.set_title('各模块类别平均进度', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 100)
        
        # 添加数值标签
        for i, (bar, progress) in enumerate(zip(bars, progress_data)):
            ax.text(progress + 2, i, f'{progress:.1f}%', 
                   va='center', fontweight='bold')
    
    def _draw_module_heatmap(self, ax):
        """绘制模块状态热力图"""
        all_modules = []
        all_progress = []
        category_labels = []
        
        for category, items in self.modules.items():
            for module_name, info in items.items():
                all_modules.append(f"{category}\n{module_name}")
                all_progress.append(info["progress"])
                category_labels.append(category)
        
        # 创建热力图数据
        rows = 6  # 每行显示的模块数
        cols = (len(all_modules) + rows - 1) // rows
        
        heatmap_data = np.zeros((rows, cols))
        module_labels = [[""] * cols for _ in range(rows)]
        
        for i, progress in enumerate(all_progress):
            row = i % rows
            col = i // rows
            if col < cols:
                heatmap_data[row, col] = progress
                module_labels[row][col] = all_modules[i].split('\n')[1][:8] + ".." if len(all_modules[i].split('\n')[1]) > 8 else all_modules[i].split('\n')[1]
        
        im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        
        # 设置标签
        ax.set_xticks(range(cols))
        ax.set_yticks(range(rows))
        
        # 添加文本标签
        for i in range(rows):
            for j in range(cols):
                if module_labels[i][j]:
                    text = ax.text(j, i, f'{module_labels[i][j]}\n{heatmap_data[i, j]:.0f}%',
                                 ha="center", va="center", fontsize=8, fontweight='bold')
        
        ax.set_title('模块进度热力图', fontsize=14, fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('完成度 (%)', rotation=270, labelpad=15)
    
    def _draw_timeline_gantt(self, ax):
        """绘制时间线甘特图"""
        # 模拟项目时间线
        timeline_data = [
            ("项目架构", "2025-01-01", "2025-01-15", "完成"),
            ("后端API", "2025-01-10", "2025-02-15", "进行中"),
            ("前端界面", "2025-01-20", "2025-03-01", "进行中"),
            ("系统集成", "2025-02-15", "2025-03-15", "待开发"),
            ("测试部署", "2025-03-01", "2025-03-20", "待开发")
        ]
        
        colors = {"完成": "#2ecc71", "进行中": "#f39c12", "待开发": "#e74c3c"}
        
        for i, (task, start, end, status) in enumerate(timeline_data):
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            duration = (end_date - start_date).days
            
            ax.barh(i, duration, left=start_date.toordinal(), 
                   color=colors[status], alpha=0.7, height=0.6)
            
            # 添加任务标签
            ax.text(start_date.toordinal() + duration/2, i, task, 
                   ha='center', va='center', fontweight='bold', fontsize=10)
        
        ax.set_yticks(range(len(timeline_data)))
        ax.set_yticklabels([item[0] for item in timeline_data])
        ax.set_title('项目时间线', fontsize=14, fontweight='bold')
        
        # 设置x轴日期格式
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        
        # 添加今天的标记线
        today = datetime.now().toordinal()
        ax.axvline(x=today, color='red', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(today, len(timeline_data)-0.5, '今天', rotation=90, 
               ha='right', va='top', color='red', fontweight='bold')
    
    def print_summary(self):
        """打印项目摘要信息"""
        print("\n" + "="*80)
        print("🚀 PG-PMC项目开发进度摘要")
        print(f"📅 最后更新: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        total_modules = 0
        completed_modules = 0
        in_progress_modules = 0
        pending_modules = 0
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for category, items in self.modules.items():
            print(f"\n📁 {category}:")
            category_lines = 0
            category_functions = 0
            category_classes = 0
            
            for module_name, info in items.items():
                status_icon = {
                    "完成": "✅",
                    "进行中": "🔄", 
                    "待开发": "⏳",
                    "待完善": "🔧",
                    "开始开发": "🚧",
                    "待检测": "❓"
                }.get(info["status"], "❓")
                
                progress_bar = "█" * (info["progress"] // 10) + "░" * (10 - info["progress"] // 10)
                
                # 显示代码统计信息
                lines = info.get("lines", 0)
                functions = info.get("functions", 0)
                classes = info.get("classes", 0)
                
                code_info = f"({lines}行/{functions}函数/{classes}类)" if lines > 0 else ""
                
                # 显示最后修改时间
                last_modified = ""
                if info.get("last_modified"):
                    try:
                        mod_time = datetime.fromisoformat(info["last_modified"])
                        days_ago = (datetime.now() - mod_time).days
                        if days_ago == 0:
                            last_modified = "今天"
                        elif days_ago == 1:
                            last_modified = "昨天"
                        else:
                            last_modified = f"{days_ago}天前"
                    except:
                        pass
                
                print(f"  {status_icon} {module_name:<25} [{progress_bar}] {info['progress']:3.0f}% {code_info:<20} {last_modified}")
                
                total_modules += 1
                category_lines += lines
                category_functions += functions
                category_classes += classes
                
                if info["status"] == "完成":
                    completed_modules += 1
                elif info["status"] in ["进行中", "开始开发"]:
                    in_progress_modules += 1
                else:
                    pending_modules += 1
            
            total_lines += category_lines
            total_functions += category_functions
            total_classes += category_classes
            
            if category_lines > 0:
                print(f"    📈 {category} 小计: {category_lines}行代码, {category_functions}个函数, {category_classes}个类")
        
        print("\n" + "="*80)
        print(f"📊 总体统计:")
        print(f"   📦 总模块数: {total_modules}")
        print(f"   ✅ 已完成: {completed_modules} ({completed_modules/total_modules*100:.1f}%)")
        print(f"   🔄 进行中: {in_progress_modules} ({in_progress_modules/total_modules*100:.1f}%)")
        print(f"   ⏳ 待开发: {pending_modules} ({pending_modules/total_modules*100:.1f}%)")
        
        overall_progress = sum(
            sum(info["progress"] for info in items.values()) 
            for items in self.modules.values()
        ) / total_modules if total_modules > 0 else 0
        
        print(f"   📈 整体进度: {overall_progress:.1f}%")
        print(f"   💻 代码统计: {total_lines}行代码, {total_functions}个函数, {total_classes}个类")
        
        # 显示最近活跃的模块
        recent_modules = []
        for category, items in self.modules.items():
            for module_name, info in items.items():
                if info.get("last_modified"):
                    try:
                        mod_time = datetime.fromisoformat(info["last_modified"])
                        recent_modules.append((module_name, mod_time, category))
                    except:
                        pass
        
        if recent_modules:
            recent_modules.sort(key=lambda x: x[1], reverse=True)
            print(f"\n   🔥 最近活跃模块:")
            for i, (module_name, mod_time, category) in enumerate(recent_modules[:5]):
                days_ago = (datetime.now() - mod_time).days
                time_str = "今天" if days_ago == 0 else f"{days_ago}天前"
                print(f"      {i+1}. {module_name} ({category}) - {time_str}")
        
        print("="*80)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PG-PMC项目开发进度看板工具')
    parser.add_argument('--update', '-u', action='store_true', help='强制更新看板数据')
    parser.add_argument('--no-chart', '-n', action='store_true', help='只显示摘要，不生成图表')
    parser.add_argument('--config', '-c', help='指定配置文件路径')
    
    args = parser.parse_args()
    
    try:
        # 获取项目根目录
        current_dir = Path(__file__).parent.parent
        
        print("🎯 PG-PMC项目开发进度看板工具 v2.0")
        print(f"📂 项目路径: {current_dir}")
        
        # 创建看板实例
        kanban = ProjectKanban(current_dir)
        
        # 如果指定了更新参数，强制更新数据
        if args.update:
            kanban.update_kanban()
        
        # 打印摘要信息
        kanban.print_summary()
        
        # 生成图形化看板（除非指定了 --no-chart）
        if not args.no_chart:
            print("\n🎨 正在生成图形化看板...")
            kanban.generate_overview_chart()
        else:
            print("\n📋 仅显示摘要信息（跳过图表生成）")
        
        print("\n💡 使用提示:")
        print("   python kb.py --update     # 强制更新看板数据")
        print("   python kb.py --no-chart   # 只显示摘要，不生成图表")
        print("   python kb.py --help       # 显示帮助信息")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()