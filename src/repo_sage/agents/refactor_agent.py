"""Refactor Agent: Generates and applies code improvements."""

import os
from typing import Any, Dict, List

from repo_sage.agents.base_agent import BaseAgent, AgentTask


class RefactorAgent(BaseAgent):
    """
    Refactor Agent responsible for:
    1. Generating refactored code based on audit findings
    2. Ensuring backward compatibility
    3. Preserving functionality while improving quality
    4. Creating diff patches for review
    """
    
    SYSTEM_PROMPT = """You are an expert software refactoring specialist.
Your task is to improve the provided code while preserving all functionality.

Guidelines:
- Maintain the exact same external behavior
- Improve readability and maintainability
- Add type hints where missing
- Add docstrings to public functions
- Reduce complexity where possible
- Use modern Python idioms (3.9+)
- Do NOT change function or class names unless necessary
- Do NOT remove any functionality

Respond with ONLY the complete refactored code inside a markdown code block.
Do not include explanations outside the code block."""

    def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process refactoring task."""
        audit_results = task.input_data.get("audit_results", [])
        auto_apply = task.input_data.get("auto_apply", False)
        output_dir = task.input_data.get("output_dir", "./refactored")
        
        # Filter high-priority items
        targets = [r for r in audit_results 
                  if r.get("refactor_priority") in ("high", "critical") 
                  and r.get("debt_score", 0) > 5]
        
        self.log(f"Planning refactoring for {len(targets)} high-priority files")
        
        refactored_files = []
        
        for i, item in enumerate(targets):
            file_path = item["file"]
            self.log(f"Refactoring [{i+1}/{len(targets)}] {file_path}")
            
            try:
                refactored_code = self._generate_refactored_code(file_path, item)
                
                if auto_apply:
                    backup_path = self._apply_refactoring(file_path, refactored_code)
                    refactored_files.append({
                        "original": file_path,
                        "backup": backup_path,
                        "status": "applied"
                    })
                else:
                    patch_path = self._save_patch(file_path, refactored_code, output_dir)
                    refactored_files.append({
                        "original": file_path,
                        "patch": patch_path,
                        "status": "patch_generated"
                    })
            
            except Exception as e:
                self.log(f"Refactoring failed for {file_path}: {e}", style="red")
                refactored_files.append({
                    "original": file_path,
                    "status": "failed",
                    "error": str(e)
                })
        
        self.log(f"Refactoring complete. {len([f for f in refactored_files if f['status'] != 'failed'])} files processed")
        
        return {
            "refactored_count": len(refactored_files),
            "files": refactored_files,
            "auto_applied": auto_apply
        }
    
    def _generate_refactored_code(self, file_path: str, audit_item: Dict) -> str:
        """Use LLM to generate refactored code."""
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Build context from audit findings
        issues_text = "\n".join([
            f"- [{issue['severity']}] {issue['description']}"
            for issue in audit_item.get("issues", [])[:5]
        ])
        
        user_prompt = f"""Refactor the following code file.

File: {file_path}

Issues to address:
{issues_text}

Original code:
```python
{original_code}
```

Provide the complete refactored file."""
        
        response = self.llm.complete(self.SYSTEM_PROMPT, user_prompt)
        
        # Extract code from markdown
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            code = response.strip()
        
        return code
    
    def _apply_refactoring(self, file_path: str, new_code: str) -> str:
        """Apply refactoring directly to file with backup."""
        backup_path = file_path + ".backup"
        
        # Create backup
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)
        
        # Write refactored code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        return backup_path
    
    def _save_patch(self, file_path: str, new_code: str, output_dir: str) -> str:
        """Save refactored code as a patch file."""
        os.makedirs(output_dir, exist_ok=True)
        
        rel_path = os.path.basename(file_path)
        patch_path = os.path.join(output_dir, f"refactored_{rel_path}")
        
        with open(patch_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        return patch_path
