"""Tests for the code analyzer module."""

import ast
import tempfile
import os

import pytest

from repo_sage.core.code_analyzer import CodeAnalyzer, analyze_project, FileAnalysis


class TestCodeAnalyzer:
    def test_analyze_simple_function(self):
        code = '''
def hello(name):
    """Say hello."""
    return f"Hello, {name}"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        
        try:
            analyzer = CodeAnalyzer(path)
            result = analyzer.analyze()
            
            assert result.lines_of_code == 4
            assert len(result.functions) == 1
            assert result.functions[0].name == "hello"
            assert result.functions[0].has_docstring is True
            assert result.functions[0].has_type_hints is False
        finally:
            os.unlink(path)
    
    def test_detect_long_function(self):
        code = '\n'.join(['def long_func():'] + ['    x = 1'] * 60 + ['    return x'])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        
        try:
            analyzer = CodeAnalyzer(path)
            result = analyzer.analyze()
            
            long_issues = [i for i in result.issues if i.rule_id == "FUNC_TOO_LONG"]
            assert len(long_issues) == 1
        finally:
            os.unlink(path)
    
    def test_detect_high_complexity(self):
        code = '''
def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "huge"
            return "big"
        return "medium"
    elif x < 0:
        if x < -10:
            return "very negative"
        return "negative"
    else:
        return "zero"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        
        try:
            analyzer = CodeAnalyzer(path)
            result = analyzer.analyze()
            
            complexity_issues = [i for i in result.issues if i.rule_id == "HIGH_COMPLEXITY"]
            assert len(complexity_issues) >= 1
        finally:
            os.unlink(path)
    
    def test_syntax_error_handling(self):
        code = 'def broken(\n    pass\n'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        
        try:
            analyzer = CodeAnalyzer(path)
            result = analyzer.analyze()
            
            assert result.ast_tree is None
            assert any(i.rule_id == "AST_ERROR" for i in result.issues)
        finally:
            os.unlink(path)


class TestAnalyzeProject:
    def test_analyze_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            with open(os.path.join(tmpdir, "file1.py"), 'w', encoding='utf-8') as f:
                f.write("def func1(): pass\n")
            
            with open(os.path.join(tmpdir, "file2.py"), 'w', encoding='utf-8') as f:
                f.write("def func2(): pass\n")
            
            # Create a non-python file
            with open(os.path.join(tmpdir, "readme.txt"), 'w', encoding='utf-8') as f:
                f.write("Hello\n")
            
            results = analyze_project(tmpdir, extensions=(".py",))
            
            assert len(results) == 2
            assert all(k.endswith('.py') for k in results.keys())
