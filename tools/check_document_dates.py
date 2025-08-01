#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档日期合规性检查工具
检查项目文档中是否存在历史日期违规问题
"""

import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class DocumentDateChecker:
    """文档日期检查器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.violations = []
        
        # 定义禁止的历史年份
        self.forbidden_years = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]
        
        # 定义日期模式
        self.date_patterns = [
            r'创建日期[：:]\s*(\d{4}年\d{1,2}月)',
            r'最后更新[：:]\s*(\d{4}年\d{1,2}月)',
            r'修改日期[：:]\s*(\d{4}年\d{1,2}月)',
            r'更新日期[：:]\s*(\d{4}年\d{1,2}月)',
            r'版本日期[：:]\s*(\d{4}年\d{1,2}月)',
            r'发布日期[：:]\s*(\d{4}年\d{1,2}月)'
        ]
    
    def get_current_year(self) -> str:
        """获取当前年份"""
        return datetime.now().strftime("%Y")
    
    def check_file_dates(self, file_path: Path) -> List[Dict]:
        """检查单个文件的日期违规"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in self.date_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    for forbidden_year in self.forbidden_years:
                        if forbidden_year in match:
                            violations.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'violation': f"发现历史日期: {match}",
                                'pattern': pattern,
                                'line_content': self._find_line_with_date(content, match)
                            })
        
        except Exception as e:
            print(f"检查文件 {file_path} 时出错: {e}")
        
        return violations
    
    def _find_line_with_date(self, content: str, date_str: str) -> str:
        """查找包含日期的行"""
        lines = content.split('\n')
        for line in lines:
            if date_str in line:
                return line.strip()
        return ""
    
    def check_all_documents(self) -> bool:
        """检查所有文档"""
        print("开始检查文档日期合规性...")
        
        # 定义需要检查的目录
        check_dirs = [
            self.docs_dir / "01-设计",
            self.docs_dir / "02-开发", 
            self.docs_dir / "03-管理"
        ]
        
        total_files = 0
        total_violations = 0
        
        for check_dir in check_dirs:
            if not check_dir.exists():
                print(f"警告: 目录不存在: {check_dir}")
                continue
            
            print(f"检查目录: {check_dir.name}")
            
            for file_path in check_dir.rglob("*.md"):
                total_files += 1
                file_violations = self.check_file_dates(file_path)
                
                if file_violations:
                    total_violations += len(file_violations)
                    self.violations.extend(file_violations)
                    print(f"错误: {file_path.name}: 发现 {len(file_violations)} 个日期违规")
                    for violation in file_violations:
                        print(f"   - {violation['violation']}")
                        if violation['line_content']:
                            print(f"     行内容: {violation['line_content']}")
        
        print(f"\n检查结果:")
        print(f"   检查文件数: {total_files}")
        print(f"   违规文件数: {len(set(v['file'] for v in self.violations))}")
        print(f"   总违规数: {total_violations}")
        
        if total_violations > 0:
            print(f"\n错误: 发现 {total_violations} 个日期违规问题")
            self._save_violations_report()
            return False
        else:
            print("\n成功: 所有文档日期检查通过")
            return True
    
    def _save_violations_report(self):
        """保存违规报告"""
        report_dir = self.project_root / "logs" / "检查报告"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"文档日期违规报告_{timestamp}.json"
        
        report_data = {
            'check_time': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'total_violations': len(self.violations),
            'violations': self.violations
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"违规报告已保存: {report_file}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    checker = DocumentDateChecker(project_root)
    
    print("=" * 60)
    print("文档日期合规性检查工具")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f"当前年份: {checker.get_current_year()}")
    print(f"禁止年份: {', '.join(checker.forbidden_years)}")
    print("=" * 60)
    
    success = checker.check_all_documents()
    
    print("=" * 60)
    
    if success:
        print("成功: 文档日期检查通过")
        sys.exit(0)
    else:
        print("错误: 文档日期检查失败")
        sys.exit(1)

if __name__ == "__main__":
    main()