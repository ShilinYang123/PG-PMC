# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from check_structure import EnhancedStructureChecker  # 假设 check_structure.py 定义了该类

def main():
    root_path = Path(__file__).parent.parent.absolute()  # 项目根目录
    whitelist_file = root_path / 'docs' / '01-设计' / '目录结构标准清单.md'
    checker = EnhancedStructureChecker(str(root_path), str(whitelist_file))
    # 执行检查
    whitelist_structure = checker.parse_whitelist()
    current_structure = checker.scan_current_structure()
    checker.compare_structures(whitelist_structure, current_structure)
    report = checker.generate_report()
    print(report)
    sys.exit(0)

if __name__ == '__main__':
    main()