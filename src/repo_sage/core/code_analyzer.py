"""Static code analysis utilities using AST."""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    rule_id: str
    message: str
    severity: str  # critical, warning, info
    line_number: int
    column: int
    suggestion: Optional[str] = None
    category: str = "general"  # complexity, style, security, performance


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line_start: int
    line_end: int
    line_count: int
    complexity: int
    parameter_count: int
    has_type_hints: bool
    has_docstring: bool
    return_type_hint: bool


@dataclass
class FileAnalysis:
    """Complete analysis result for a single file."""
    file_path: str
    lines_of_code: int
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    ast_tree: Optional[ast.AST] = None
    raw_content: str = ""


class CodeAnalyzer:
    """Python code analyzer using AST."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None
        self._tree: Optional[ast.AST] = None
    
    def _load_content(self) -> str:
        """Load file content."""
        if self._content is None:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._content = f.read()
        return self._content
    
    def _parse_ast(self) -> Optional[ast.AST]:
        """Parse file into AST."""
        if self._tree is None:
            try:
                self._tree = ast.parse(self._load_content())
            except SyntaxError:
                return None
        return self._tree
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def analyze(self) -> FileAnalysis:
        """Perform full analysis on the file."""
        content = self._load_content()
        tree = self._parse_ast()
        
        result = FileAnalysis(
            file_path=str(self.file_path),
            lines_of_code=len(content.splitlines()),
            raw_content=content,
            ast_tree=tree
        )
        
        if tree is None:
            result.issues.append(CodeIssue(
                rule_id="AST_ERROR",
                message="Failed to parse file due to syntax error",
                severity="critical",
                line_number=0,
                column=0
            ))
            return result
        
        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    result.imports.append(alias.name)
        
        # Analyze functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                result.classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                func_metrics = self._analyze_function(node)
                result.functions.append(func_metrics)
                
                # Check for issues
                if func_metrics.line_count > 50:
                    result.issues.append(CodeIssue(
                        rule_id="FUNC_TOO_LONG",
                        message=f"Function '{func_metrics.name}' is too long ({func_metrics.line_count} lines)",
                        severity="warning",
                        line_number=func_metrics.line_start,
                        column=0,
                        suggestion="Consider breaking this function into smaller, focused functions",
                        category="complexity"
                    ))
                
                if func_metrics.complexity > 10:
                    result.issues.append(CodeIssue(
                        rule_id="HIGH_COMPLEXITY",
                        message=f"Function '{func_metrics.name}' has high cyclomatic complexity ({func_metrics.complexity})",
                        severity="warning",
                        line_number=func_metrics.line_start,
                        column=0,
                        suggestion="Refactor to reduce branching logic",
                        category="complexity"
                    ))
                
                if not func_metrics.has_type_hints:
                    result.issues.append(CodeIssue(
                        rule_id="MISSING_TYPE_HINTS",
                        message=f"Function '{func_metrics.name}' parameters lack type hints",
                        severity="info",
                        line_number=func_metrics.line_start,
                        column=0,
                        suggestion="Add type annotations for better code clarity",
                        category="style"
                    ))
                
                if not func_metrics.has_docstring:
                    result.issues.append(CodeIssue(
                        rule_id="MISSING_DOCSTRING",
                        message=f"Function '{func_metrics.name}' lacks a docstring",
                        severity="info",
                        line_number=func_metrics.line_start,
                        column=0,
                        suggestion="Add a descriptive docstring explaining purpose and parameters",
                        category="style"
                    ))
        
        return result
    
    def _analyze_function(self, node: ast.FunctionDef) -> FunctionMetrics:
        """Analyze a single function definition."""
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        
        # Check type hints
        has_type_hints = any(arg.annotation for arg in node.args.args + node.args.kwonlyargs)
        return_type_hint = node.returns is not None
        
        # Check docstring
        has_docstring = False
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            has_docstring = True
        
        return FunctionMetrics(
            name=node.name,
            line_start=line_start,
            line_end=line_end,
            line_count=line_end - line_start + 1,
            complexity=self._calculate_complexity(node),
            parameter_count=len(node.args.args) + len(node.args.kwonlyargs),
            has_type_hints=has_type_hints or return_type_hint,
            has_docstring=has_docstring,
            return_type_hint=return_type_hint
        )


def analyze_project(project_path: str, extensions: tuple = (".py",)) -> Dict[str, FileAnalysis]:
    """Analyze all files in a project directory."""
    results = {}
    project = Path(project_path)
    
    for ext in extensions:
        for file_path in project.rglob(f"*{ext}"):
            # Skip common non-source directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
            
            try:
                analyzer = CodeAnalyzer(str(file_path))
                results[str(file_path)] = analyzer.analyze()
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
    
    return results
