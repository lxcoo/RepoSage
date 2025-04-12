"""Explorer Agent: Discovers and maps repository structure."""

import os
from pathlib import Path
from typing import Any, Dict, List, Set

from repo_sage.agents.base_agent import BaseAgent, AgentTask


class ExplorerAgent(BaseAgent):
    """
    Explorer Agent responsible for:
    1. Traversing the repository structure
    2. Identifying source files and their relationships
    3. Building a dependency graph
    4. Determining analysis scope
    """
    
    def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process exploration task."""
        repo_path = task.input_data.get("repo_path", ".")
        extensions = tuple(task.input_data.get("extensions", [".py"]))
        
        self.log(f"Exploring repository: {repo_path}")
        
        # Discover files
        files = self._discover_files(repo_path, extensions)
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(files)
        
        # Identify entry points and modules
        modules = self._identify_modules(repo_path, files)
        
        result = {
            "total_files": len(files),
            "files": files,
            "modules": modules,
            "dependency_graph": dependencies,
            "repository_root": os.path.abspath(repo_path)
        }
        
        self.log(f"Discovered {len(files)} source files across {len(modules)} modules")
        return result
    
    def _discover_files(self, repo_path: str, extensions: tuple) -> List[str]:
        """Discover all source files in the repository."""
        files = []
        repo = Path(repo_path)
        
        if not repo.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 
                        '.pytest_cache', 'build', 'dist', '.idea', '.vscode'}
        
        for root, dirs, filenames in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, filename)
                    # Skip very large files (>500KB)
                    if os.path.getsize(full_path) < 500 * 1024:
                        files.append(os.path.abspath(full_path))
        
        return sorted(files)
    
    def _build_dependency_graph(self, files: List[str]) -> Dict[str, List[str]]:
        """Build a simple dependency graph based on imports."""
        dependencies = {}
        
        for file_path in files:
            deps = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple regex-free import detection for Python
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Extract module name
                        parts = line.split()
                        if len(parts) >= 2:
                            module = parts[1].split('.')[0]
                            if module not in ('os', 'sys', 'json', 'typing', 'pathlib',
                                            'abc', 'dataclasses', 'collections'):
                                deps.append(module)
            except Exception:
                pass
            
            dependencies[file_path] = list(set(deps))
        
        return dependencies
    
    def _identify_modules(self, repo_path: str, files: List[str]) -> List[Dict[str, Any]]:
        """Identify high-level modules in the project."""
        repo = Path(repo_path).resolve()
        module_map: Dict[str, Set[str]] = {}
        
        for file_path in files:
            rel_path = Path(file_path).relative_to(repo)
            top_dir = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
            
            if top_dir not in module_map:
                module_map[top_dir] = set()
            module_map[top_dir].add(str(rel_path))
        
        modules = []
        for name, file_set in module_map.items():
            modules.append({
                "name": name,
                "file_count": len(file_set),
                "files": sorted(file_set)[:10]  # Limit for brevity
            })
        
        return sorted(modules, key=lambda x: x["file_count"], reverse=True)
