"""Tests for calculator module."""

import pytest
import math
from demo_repo.calculator import calc, DataProcessor, legacy_api_fetch


class TestCalc:
    def test_add(self):
        assert calc(2, 3, "add") == 5
        assert calc(-1, 1, "add") == 0
    
    def test_sub(self):
        assert calc(5, 3, "sub") == 2
        assert calc(3, 5, "sub") == -2
    
    def test_mul(self):
        assert calc(4, 5, "mul") == 20
        assert calc(0, 100, "mul") == 0
    
    def test_div(self):
        assert calc(10, 2, "div") == 5.0
        with pytest.raises(ValueError):
            calc(10, 0, "div")
    
    def test_pow(self):
        assert calc(2, 3, "pow") == 8
        assert calc(5, 0, "pow") == 1
    
    def test_sqrt(self):
        assert calc(9, 0, "sqrt") == 3.0
        with pytest.raises(ValueError):
            calc(-1, 0, "sqrt")
    
    def test_fact(self):
        assert calc(5, 0, "fact") == 120
        assert calc(0, 0, "fact") == 1
        with pytest.raises(ValueError):
            calc(-1, 0, "fact")
    
    def test_log(self):
        assert calc(math.e, 0, "log") == pytest.approx(1.0)
        with pytest.raises(ValueError):
            calc(-1, 0, "log")
    
    def test_unknown_op(self):
        with pytest.raises(ValueError):
            calc(1, 2, "unknown")


class TestDataProcessor:
    def test_process_integers(self):
        dp = DataProcessor([1, 2, 3, 4])
        result = dp.process()
        assert result == [3, 4, 9, 8]
    
    def test_process_strings(self):
        dp = DataProcessor(["hi", "hello world"])
        result = dp.process()
        assert result == ["hi", "HELLO WORLD"]
    
    def test_process_mixed(self):
        dp = DataProcessor([1, "test", 3.14159])
        result = dp.process()
        assert result[0] == 3
        assert result[1] == "test"
        assert result[2] == 3.14
    
    def test_get_stats(self):
        dp = DataProcessor([1, 2, 3, 4])
        dp.process()
        stats = dp.get_stats()
        assert stats["count"] == 4
        assert stats["total"] == 18
        assert stats["avg"] == 4.5
    
    def test_empty_stats(self):
        dp = DataProcessor([])
        stats = dp.get_stats()
        assert stats["avg"] == 0
