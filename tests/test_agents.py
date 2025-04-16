"""Tests for the agent system."""

import os
import tempfile
from pathlib import Path

import pytest

from repo_sage.agents.base_agent import BaseAgent, AgentTask
from repo_sage.agents.explorer_agent import ExplorerAgent
from repo_sage.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response='{"issues": [], "technical_debt_score": 5}'):
        self.response = response
    
    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return self.response
    
    def chat(self, messages: list, **kwargs) -> str:
        return self.response


class TestExplorerAgent:
    def test_discover_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "tests").mkdir()
            
            with open(os.path.join(tmpdir, "src", "main.py"), 'w', encoding='utf-8') as f:
                f.write("print('hello')\n")
            
            with open(os.path.join(tmpdir, "tests", "test_main.py"), 'w', encoding='utf-8') as f:
                f.write("def test(): pass\n")
            
            llm = MockLLMProvider()
            agent = ExplorerAgent("Explorer", llm)
            
            task = AgentTask(
                task_id="test-1",
                task_type="explore",
                input_data={"repo_path": tmpdir, "extensions": [".py"]},
                context={}
            )
            
            result = agent.execute_task(task)
            
            assert result.status == "completed"
            assert result.result["total_files"] == 2
            assert any("main.py" in f for f in result.result["files"])
    
    def test_skip_venv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "venv").mkdir()
            Path(tmpdir, "src").mkdir()
            
            with open(os.path.join(tmpdir, "venv", "lib.py"), 'w', encoding='utf-8') as f:
                f.write("# venv file\n")
            
            with open(os.path.join(tmpdir, "src", "app.py"), 'w', encoding='utf-8') as f:
                f.write("print('app')\n")
            
            llm = MockLLMProvider()
            agent = ExplorerAgent("Explorer", llm)
            
            task = AgentTask(
                task_id="test-2",
                task_type="explore",
                input_data={"repo_path": tmpdir, "extensions": [".py"]},
                context={}
            )
            
            result = agent.execute_task(task)
            
            assert result.result["total_files"] == 1
            assert all("venv" not in f for f in result.result["files"])
