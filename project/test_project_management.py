#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理功能测试脚本
测试AI驱动程序的项目识别和管理能力
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai.intelligent_scheduler import IntelligentScheduler
from src.utils.logger import get_logger


def test_project_management():
    """测试项目管理功能"""
    logger = get_logger("ProjectManagementTest")
    
    try:
        # 初始化智能调度器
        scheduler = IntelligentScheduler()
        
        # 测试用例
        test_cases = [
            "创建新项目：智能咖啡机开发",
            "切换到项目：智能咖啡机开发",
            "在当前项目中创建一个圆柱体，直径50mm，高度100mm",
            "列出所有项目",
            "更新项目信息：智能咖啡机开发，状态为进行中",
            "画一个长方体，长度100mm，宽度50mm，高度30mm",
            "项目归档：智能咖啡机开发"
        ]
        
        logger.info("开始测试项目管理功能...")
        
        for i, test_input in enumerate(test_cases, 1):
            logger.info(f"\n=== 测试用例 {i} ===")
            logger.info(f"输入: {test_input}")
            
            # 处理用户输入
            result = scheduler.process_user_input(test_input)
            
            logger.info(f"输入类型: {result.get('input_type', 'unknown')}")
            logger.info(f"处理结果: {result.get('success', False)}")
            
            if result.get('success'):
                if result.get('input_type') == 'project_management':
                    logger.info(f"项目操作: {result.get('operation', 'unknown')}")
                    logger.info(f"消息: {result.get('message', '')}")
                elif result.get('input_type') == 'design_instruction':
                    design_info = result.get('design_instruction', {})
                    logger.info(f"设计意图: {design_info.get('intent', 'unknown')}")
                    logger.info(f"置信度: {result.get('confidence', 0)}")
                elif result.get('input_type') == 'mixed':
                    logger.info("检测到混合指令")
                    logger.info(f"项目结果: {result.get('project_result', {})}")
                    logger.info(f"设计结果: {result.get('design_result', {})}")
            else:
                logger.warning(f"处理失败: {result.get('error', 'unknown error')}")
            
            # 显示当前项目上下文
            context = scheduler.get_current_project_context()
            if context.get('has_current_project'):
                project_info = context.get('project_info', {})
                logger.info(f"当前项目: {project_info.get('name', 'unknown')}")
            else:
                logger.info("当前没有选择项目")
        
        # 测试系统状态
        logger.info("\n=== 系统状态 ===")
        status = scheduler.get_system_status()
        for key, value in status.items():
            logger.info(f"{key}: {value}")
        
        # 测试AI建议
        logger.info("\n=== AI建议测试 ===")
        suggestions = scheduler.get_ai_suggestions("我想创建一个新项目")
        for suggestion in suggestions:
            logger.info(f"建议: {suggestion}")
        
        logger.info("\n✅ 项目管理功能测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_project_management()