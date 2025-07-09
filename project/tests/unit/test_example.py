"""示例测试文件

这是一个基础的测试文件模板，展示了如何编写单元测试。
"""

import pytest
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestExample:
    """示例测试类"""

    def test_basic_assertion(self):
        """测试基本断言"""
        assert True
        assert 1 == 1
        assert "hello" == "hello"

    def test_addition(self):
        """测试加法运算"""
        result = 2 + 2
        assert result == 4

    def test_string_operations(self):
        """测试字符串操作"""
        text = "PinGao工作室"
        assert len(text) == 7
        assert "PinGao" in text

    def test_list_operations(self):
        """测试列表操作"""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert 3 in test_list
        assert test_list[0] == 1

    def test_exception_handling(self):
        """测试异常处理"""
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0  # Assign to _ to indicate it's intentionally unused

    @pytest.mark.parametrize("input_value,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (4, 8),
    ])
    def test_parametrized(self, input_value, expected):
        """参数化测试示例"""
        result = input_value * 2
        assert result == expected


def test_function_example():
    """函数式测试示例"""
    data = {"name": "PinGao", "type": "工作室"}
    assert data["name"] == "PinGao"
    assert "type" in data


@pytest.fixture
def sample_data():
    """测试数据fixture"""
    return {
        "users": ["张三", "李四", "王五"],
        "config": {"debug": True, "version": "1.0.0"}
    }


def test_with_fixture(sample_data):
    """使用fixture的测试"""
    assert len(sample_data["users"]) == 3
    assert sample_data["config"]["debug"] is True
    assert sample_data["config"]["version"] == "1.0.0"
