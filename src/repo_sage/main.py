"""CLI entry point for RepoSage."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from repo_sage.agents.explorer_agent import ExplorerAgent
from repo_sage.agents.auditor_agent import AuditorAgent
from repo_sage.agents.refactor_agent import RefactorAgent
from repo_sage.agents.verifier_agent import VerifierAgent
from repo_sage.llm.provider import get_provider
from repo_sage.core.config import settings

app = typer.Typer(help="RepoSage: Multi-Agent Intelligent Codebase Governance")
console = Console()


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║  RepoSage - Multi-Agent Intelligent Codebase Governance   ║
    ║                                                           ║
    ║  🤖 Explorer → 🔍 Auditor → 🔧 Refactor → ✅ Verifier    ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold cyan"))


@app.command()
def analyze(
    repo_path: str = typer.Argument(".", help="Path to the repository to analyze"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider (openai, anthropic)"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model name"),
    auto_refactor: bool = typer.Option(False, "--auto-refactor", help="Automatically apply refactoring"),
    output: str = typer.Option("./reports", "--output", "-o", help="Output directory for reports"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for LLM provider"),
    max_files: int = typer.Option(50, "--max-files", help="Maximum files to analyze")
):
    """Run the full RepoSage analysis pipeline."""
    print_banner()
    
    # Validate path
    repo = Path(repo_path).resolve()
    if not repo.exists():
        console.print(f"[red]Error: Repository path does not exist: {repo}[/red]")
        raise typer.Exit(1)
    
    # Initialize LLM provider
    try:
        llm = get_provider(
            provider_name=provider,
            api_key=api_key,
            model=model
        )
        console.print(f"[green]✓[/green] Initialized {provider} provider with model {model}")
    except Exception as e:
        console.print(f"[red]Error initializing LLM provider: {e}[/red]")
        raise typer.Exit(1)
    
    # Stage 1: Exploration
    console.print("\n[bold yellow]📂 Stage 1: Repository Exploration[/bold yellow]")
    explorer = ExplorerAgent("Explorer", llm, console)
    explore_task = explorer.execute_task(explorer._create_task({
        "repo_path": str(repo),
        "extensions": list(settings.target_extensions)
    }))
    
    files = explore_task.result.get("files", [])[:max_files]
    console.print(f"  Discovered [bold]{len(files)}[/bold] files to analyze")
    
    # Stage 2: Auditing
    console.print("\n[bold yellow]🔍 Stage 2: Deep Code Audit[/bold yellow]")
    auditor = AuditorAgent("Auditor", llm, console)
    audit_task = auditor.execute_task(auditor._create_task({
        "files": files
    }))
    
    # Display summary
    total_issues = audit_task.result.get("total_issues", 0)
    critical = audit_task.result.get("critical_issues", 0)
    console.print(f"  Found [bold red]{critical}[/bold red] critical, [bold]{total_issues}[/bold] total issues")
    
    # Stage 3: Refactoring
    console.print("\n[bold yellow]🔧 Stage 3: Intelligent Refactoring[/bold yellow]")
    refactor = RefactorAgent("Refactor", llm, console)
    refactor_task = refactor.execute_task(refactor._create_task({
        "audit_results": audit_task.result.get("results", []),
        "auto_apply": auto_refactor,
        "output_dir": output
    }))
    
    refactored = refactor_task.result.get("refactored_count", 0)
    console.print(f"  Processed [bold]{refactored}[/bold] high-priority files")
    
    # Stage 4: Verification
    console.print("\n[bold yellow]✅ Stage 4: Verification & Testing[/bold yellow]")
    verifier = VerifierAgent("Verifier", llm, console)
    verify_task = verifier.execute_task(verifier._create_task({
        "files": refactor_task.result.get("files", []),
        "repo_path": str(repo),
        "test_command": "pytest"
    }))
    
    passed = verify_task.result.get("passed_count", 0)
    total = verify_task.result.get("total_count", 0)
    console.print(f"  [bold green]{passed}/{total}[/bold green] verifications passed")
    
    # Generate report
    console.print("\n[bold yellow]📊 Generating Report...[/bold yellow]")
    _generate_report(repo, output, explore_task.result, audit_task.result, 
                     refactor_task.result, verify_task.result)
    
    console.print(f"\n[bold green]✨ Analysis complete! Report saved to {output}/report.md[/bold green]")


def _generate_report(repo, output_dir, explore, audit, refactor, verify):
    """Generate markdown report."""
    os.makedirs(output_dir, exist_ok=True)
    
    report = f"""# RepoSage Analysis Report

**Repository:** `{repo}`  
**Generated:** Automatically via Multi-Agent Pipeline

## 📂 Repository Overview

- **Total Files Analyzed:** {explore.get('total_files', 0)}
- **Modules:** {len(explore.get('modules', []))}

## 🔍 Audit Summary

- **Total Issues:** {audit.get('total_issues', 0)}
- **Critical Issues:** {audit.get('critical_issues', 0)}
- **Top Priority Files:** {', '.join(audit.get('top_priority_files', [])[:3])}

## 🔧 Refactoring

- **Files Processed:** {refactor.get('refactored_count', 0)}
- **Auto-Applied:** {refactor.get('auto_applied', False)}

## ✅ Verification

- **Passed:** {verify.get('passed_count', 0)} / {verify.get('total_count', 0)}
- **Recommendation:** {verify.get('recommendation', 'review')}

## 🎯 Next Steps

1. Review critical issues in the audit report
2. Apply suggested refactoring patches
3. Run full test suite before merging

---
*Generated by RepoSage - Multi-Agent Intelligent Codebase Governance*
"""
    
    with open(os.path.join(output_dir, "report.md"), 'w', encoding='utf-8') as f:
        f.write(report)


# Helper to create tasks from dict (monkey-patch for CLI usage)
def _create_task(self, input_data):
    from repo_sage.agents.base_agent import AgentTask
    import uuid
    return AgentTask(
        task_id=str(uuid.uuid4())[:8],
        task_type="generic",
        input_data=input_data,
        context={}
    )

ExplorerAgent._create_task = _create_task
AuditorAgent._create_task = _create_task
RefactorAgent._create_task = _create_task
VerifierAgent._create_task = _create_task


if __name__ == "__main__":
    app()
