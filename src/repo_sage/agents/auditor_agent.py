"""Auditor Agent: Performs deep code audit using static analysis + LLM."""

import json
from typing import Any, Dict, List

from repo_sage.agents.base_agent import BaseAgent, AgentTask
from repo_sage.core.code_analyzer import CodeAnalyzer, FileAnalysis


class AuditorAgent(BaseAgent):
    """
    Auditor Agent responsible for:
    1. Running static analysis on each file
    2. Using LLM for deep semantic analysis
    3. Identifying technical debt, security issues, and design smells
    4. Prioritizing issues by severity and impact
    """
    
    SYSTEM_PROMPT = """You are an expert software architect and code reviewer. 
Analyze the provided code file and identify technical debt, design issues, and improvement opportunities.

Respond in JSON format with this structure:
{
  "technical_debt_score": 1-10,
  "issues": [
    {
      "category": "complexity|security|performance|maintainability|design",
      "severity": "critical|high|medium|low",
      "description": "Detailed description of the issue",
      "location": "function or line reference",
      "impact": "Why this matters",
      "recommendation": "Specific fix recommendation"
    }
  ],
  "strengths": ["What's good about this code"],
  "refactor_priority": "high|medium|low",
  "estimated_effort": "small|medium|large"
}

Be thorough but concise. Focus on actionable issues."""

    def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process audit task."""
        files = task.input_data.get("files", [])
        context = task.context
        
        self.log(f"Starting deep audit of {len(files)} files")
        
        audit_results = []
        total_issues = 0
        critical_count = 0
        
        for i, file_path in enumerate(files):
            self.log(f"Auditing [{i+1}/{len(files)}] {file_path}")
            
            # Static analysis
            try:
                analyzer = CodeAnalyzer(file_path)
                static_result = analyzer.analyze()
            except Exception as e:
                self.log(f"Static analysis failed for {file_path}: {e}", style="yellow")
                static_result = None
            
            # LLM deep analysis
            llm_result = self._llm_audit(file_path, static_result)
            
            # Combine results
            combined = self._merge_results(file_path, static_result, llm_result)
            audit_results.append(combined)
            
            total_issues += len(combined.get("issues", []))
            critical_count += sum(1 for issue in combined.get("issues", []) 
                                 if issue.get("severity") == "critical")
        
        # Prioritize files by debt score
        audit_results.sort(key=lambda x: x.get("debt_score", 0), reverse=True)
        
        self.log(f"Audit complete. Found {total_issues} issues ({critical_count} critical)")
        
        return {
            "audited_files": len(files),
            "total_issues": total_issues,
            "critical_issues": critical_count,
            "results": audit_results,
            "top_priority_files": [r["file"] for r in audit_results[:5]]
        }
    
    def _llm_audit(self, file_path: str, static_result: FileAnalysis = None) -> Dict[str, Any]:
        """Use LLM for deep semantic analysis of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        # Truncate very large files
        if len(code) > 8000:
            code = code[:8000] + "\n\n[File truncated due to length...]"
        
        static_summary = ""
        if static_result:
            static_summary = f"""
Static Analysis Summary:
- Lines of code: {static_result.lines_of_code}
- Functions: {len(static_result.functions)}
- AST Issues: {len(static_result.issues)}
"""
        
        user_prompt = f"""Please audit the following code file.

File: {file_path}

{static_summary}

```python
{code}
```

Provide your analysis in the requested JSON format."""
        
        try:
            return self._llm_json_completion(self.SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            self.log(f"LLM audit failed for {file_path}: {e}", style="yellow")
            return {"error": str(e), "issues": []}
    
    def _merge_results(self, file_path: str, static: FileAnalysis, llm: Dict) -> Dict[str, Any]:
        """Merge static and LLM analysis results."""
        issues = []
        
        # Add static analysis issues
        if static:
            for issue in static.issues:
                issues.append({
                    "category": issue.category,
                    "severity": "medium" if issue.severity == "warning" else "low",
                    "description": issue.message,
                    "location": f"line {issue.line_number}",
                    "impact": "Code quality and maintainability",
                    "recommendation": issue.suggestion or "Review and fix",
                    "source": "static"
                })
        
        # Add LLM issues
        for issue in llm.get("issues", []):
            issue["source"] = "llm"
            issues.append(issue)
        
        # Calculate combined debt score
        static_score = len([i for i in (static.issues if static else []) 
                           if i.severity == "warning"]) * 0.5
        llm_score = llm.get("technical_debt_score", 5)
        debt_score = min(10, (llm_score + static_score / 10))
        
        return {
            "file": file_path,
            "debt_score": round(debt_score, 1),
            "issues": issues,
            "strengths": llm.get("strengths", []),
            "refactor_priority": llm.get("refactor_priority", "medium"),
            "estimated_effort": llm.get("estimated_effort", "medium"),
            "lines_of_code": static.lines_of_code if static else 0
        }
