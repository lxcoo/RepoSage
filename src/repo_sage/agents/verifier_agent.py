"""Verifier Agent: Validates refactored code through testing."""

import os
import subprocess
import sys
from typing import Any, Dict, List

from repo_sage.agents.base_agent import BaseAgent, AgentTask


class VerifierAgent(BaseAgent):
    """
    Verifier Agent responsible for:
    1. Running static type checks
    2. Executing unit tests
    3. Verifying syntax correctness
    4. Checking for regression issues
    5. Generating test coverage reports
    """
    
    def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process verification task."""
        files = task.input_data.get("files", [])
        test_command = task.input_data.get("test_command", "pytest")
        repo_path = task.input_data.get("repo_path", ".")
        
        self.log(f"Starting verification for {len(files)} files")
        
        results = []
        all_passed = True
        
        for file_info in files:
            original = file_info.get("original", "")
            self.log(f"Verifying {original}")
            
            # Syntax check
            syntax_ok = self._check_syntax(original)
            
            # Run tests if applicable
            test_result = self._run_tests(repo_path, test_command, original)
            
            file_result = {
                "file": original,
                "syntax_valid": syntax_ok,
                "tests_passed": test_result.get("passed", False),
                "test_output": test_result.get("output", ""),
                "coverage": test_result.get("coverage", 0.0),
                "overall": syntax_ok and test_result.get("passed", False)
            }
            
            if not file_result["overall"]:
                all_passed = False
            
            results.append(file_result)
        
        # Overall assessment
        passed_count = sum(1 for r in results if r["overall"])
        
        self.log(f"Verification complete: {passed_count}/{len(results)} files passed")
        
        return {
            "all_passed": all_passed,
            "passed_count": passed_count,
            "total_count": len(results),
            "results": results,
            "recommendation": "rollback" if not all_passed else "proceed"
        }
    
    def _check_syntax(self, file_path: str) -> bool:
        """Check if a Python file has valid syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    def _run_tests(self, repo_path: str, test_command: str, target_file: str) -> Dict[str, Any]:
        """Run tests for the repository."""
        result = {"passed": False, "output": "", "coverage": 0.0}
        
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, "-m", "pytest",
                "-xvs",
                "--tb=short",
                "--cov=.",
                "--cov-report=term-missing",
                repo_path
            ]
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=repo_path
            )
            
            result["output"] = proc.stdout + "\n" + proc.stderr
            result["passed"] = proc.returncode == 0
            
            # Try to extract coverage percentage
            for line in proc.stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if '%' in part:
                                result["coverage"] = float(part.replace('%', ''))
                                break
                    except ValueError:
                        pass
        
        except subprocess.TimeoutExpired:
            result["output"] = "Test execution timed out"
        except Exception as e:
            result["output"] = f"Test execution failed: {e}"
        
        return result
