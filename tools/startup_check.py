# -*- coding: utf-8 -*-

import sys
from start import AIAssistantStartupChecker  # 假设 start.py 仍存在或调整
import traceback

def main():
    try:
        checker = AIAssistantStartupChecker()
        success, message = checker.perform_startup_check()
        print(message)
        sys.exit(0 if success else 2)
    except Exception as e:
        print(f'启动检查失败: {str(e)}')
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    main()