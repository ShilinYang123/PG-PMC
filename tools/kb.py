#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC项目开发进度看板工具
功能：图形化展示项目所有功能模块的开发状态
作者：雨俊
创建时间：2025-01-20
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ProjectKanban:
    """项目看板类"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.modules = self._load_module_status()
        
    def _load_module_status(self) -> Dict:
        """加载模块状态信息"""
        modules = {
            "后端API模块": {
                "用户认证模块": {"status": "完成", "progress": 100, "files": ["auth.py"]},
                "设备管理模块": {"status": "完成", "progress": 100, "files": ["equipment.py"]},
                "质量管理模块": {"status": "完成", "progress": 100, "files": ["quality.py"]},
                "物料管理模块": {"status": "进行中", "progress": 70, "files": ["materials.py"]},
                "订单管理模块": {"status": "进行中", "progress": 60, "files": ["orders.py"]},
                "生产计划模块": {"status": "进行中", "progress": 50, "files": ["production_plans.py"]},
                "进度跟踪模块": {"status": "进行中", "progress": 40, "files": ["progress.py"]},
                "用户管理模块": {"status": "完成", "progress": 100, "files": ["users.py"]}
            },
            "前端界面模块": {
                "仪表板页面": {"status": "完成", "progress": 80, "files": ["Dashboard/index.tsx"]},
                "订单管理页面": {"status": "进行中", "progress": 60, "files": ["OrderManagement/index.tsx"]},
                "生产计划页面": {"status": "进行中", "progress": 50, "files": ["ProductionPlan/index.tsx"]},
                "物料管理页面": {"status": "进行中", "progress": 60, "files": ["MaterialManagement/index.tsx"]},
                "进度跟踪页面": {"status": "进行中", "progress": 40, "files": ["ProgressTracking/index.tsx"]},
                "图表组件库": {"status": "待开发", "progress": 20, "files": []},
                "移动端适配": {"status": "待开发", "progress": 0, "files": []},
                "通知组件": {"status": "待开发", "progress": 0, "files": []}
            },
            "数据模型层": {
                "订单模型": {"status": "完成", "progress": 100, "files": ["order.py"]},
                "生产计划模型": {"status": "完成", "progress": 100, "files": ["production_plan.py"]},
                "物料模型": {"status": "完成", "progress": 100, "files": ["material.py"]},
                "进度记录模型": {"status": "完成", "progress": 100, "files": ["progress.py"]},
                "用户模型": {"status": "完成", "progress": 100, "files": ["user.py"]},
                "质量记录模型": {"status": "待完善", "progress": 80, "files": []},
                "设备模型": {"status": "待开发", "progress": 0, "files": []}
            },
            "系统集成模块": {
                "通知催办系统": {"status": "待开发", "progress": 0, "files": []},
                "微信集成": {"status": "待开发", "progress": 0, "files": []},
                "邮件系统": {"status": "待开发", "progress": 0, "files": []},
                "短信通知": {"status": "待开发", "progress": 0, "files": []},
                "文件导入导出": {"status": "待开发", "progress": 10, "files": []},
                "数据备份恢复": {"status": "待开发", "progress": 0, "files": []}
            }
        }
        
        # 检查实际文件存在情况
        self._verify_file_existence(modules)
        return modules
    
    def _verify_file_existence(self, modules: Dict):
        """验证文件是否实际存在"""
        backend_path = self.project_root / "project" / "backend" / "app"
        frontend_path = self.project_root / "project" / "frontend" / "src"
        
        for category, items in modules.items():
            for module_name, info in items.items():
                if info["files"]:
                    for file_name in info["files"]:
                        if category == "后端API模块":
                            file_path = backend_path / "api" / "endpoints" / file_name
                        elif category == "前端界面模块":
                            file_path = frontend_path / "pages" / file_name
                        elif category == "数据模型层":
                            file_path = backend_path / "models" / file_name
                        else:
                            continue
                            
                        if not file_path.exists():
                            info["progress"] = max(0, info["progress"] - 20)
                            if info["progress"] < 50:
                                info["status"] = "待开发"
    
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
        print("\n" + "="*60)
        print("🚀 PG-PMC项目开发进度摘要")
        print("="*60)
        
        total_modules = 0
        completed_modules = 0
        in_progress_modules = 0
        pending_modules = 0
        
        for category, items in self.modules.items():
            print(f"\n📁 {category}:")
            for module_name, info in items.items():
                status_icon = {
                    "完成": "✅",
                    "进行中": "🔄", 
                    "待开发": "⏳",
                    "待完善": "🔧"
                }[info["status"]]
                
                progress_bar = "█" * (info["progress"] // 10) + "░" * (10 - info["progress"] // 10)
                print(f"  {status_icon} {module_name:<20} [{progress_bar}] {info['progress']:3.0f}%")
                
                total_modules += 1
                if info["status"] == "完成":
                    completed_modules += 1
                elif info["status"] == "进行中":
                    in_progress_modules += 1
                else:
                    pending_modules += 1
        
        print("\n" + "="*60)
        print(f"📊 总体统计:")
        print(f"   总模块数: {total_modules}")
        print(f"   已完成: {completed_modules} ({completed_modules/total_modules*100:.1f}%)")
        print(f"   进行中: {in_progress_modules} ({in_progress_modules/total_modules*100:.1f}%)")
        print(f"   待开发: {pending_modules} ({pending_modules/total_modules*100:.1f}%)")
        
        overall_progress = sum(
            sum(info["progress"] for info in items.values()) 
            for items in self.modules.values()
        ) / total_modules
        
        print(f"   整体进度: {overall_progress:.1f}%")
        print("="*60)

def main():
    """主函数"""
    try:
        # 获取项目根目录
        current_dir = Path(__file__).parent.parent
        
        print("🎯 PG-PMC项目开发进度看板工具")
        print(f"📂 项目路径: {current_dir}")
        
        # 创建看板实例
        kanban = ProjectKanban(current_dir)
        
        # 打印摘要信息
        kanban.print_summary()
        
        # 生成图形化看板
        print("\n🎨 正在生成图形化看板...")
        kanban.generate_overview_chart()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()