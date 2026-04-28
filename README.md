# RepoSage 🌿

> **Multi-Agent Intelligent Codebase Governance System**

RepoSage is an AI-driven code quality governance platform that leverages multiple specialized agents to analyze, audit, refactor, and verify codebases automatically. Built for engineering teams who want to systematically eliminate technical debt without sacrificing development velocity.

## 🎯 Why RepoSage?

Modern codebases accumulate technical debt at an accelerating pace. Traditional static analysis tools catch syntax issues but miss semantic problems, architectural smells, and context-specific design flaws. RepoSage bridges this gap by combining **deep static analysis** with **LLM-powered semantic understanding** in a coordinated multi-agent pipeline.

## 🏗️ Architecture

RepoSage employs a **multi-agent collaboration pattern** where specialized agents communicate through a shared message bus to perform complex, long-chain reasoning tasks:

```
┌─────────────────────────────────────────────────────────────────┐
│                      RepoSage Pipeline                           │
├─────────────┐    ┌─────────────┐    ┌─────────────┐   ┌────────┤
│  📂 Explorer │───→│  🔍 Auditor  │───→│  🔧 Refactor│──→│✅ Verify│
│  Agent       │    │  Agent       │    │  Agent      │   │ Agent  │
└─────────────┘    └─────────────┘    └─────────────┘   └────────┘
     │                   │                    │                │
     ▼                   ▼                    ▼                ▼
  File Discovery    Deep Analysis        Code Generation    Test &
  Dependency Map    Tech Debt Score      Patch/Diff         Validation
  Module Detection  Priority Queue       Backward Compat    Coverage
```

### Agent Capabilities

| Agent | Responsibility | Key Features |
|-------|---------------|--------------|
| **Explorer** | Repository mapping | Dependency graph construction, module detection, scope filtering |
| **Auditor** | Deep code analysis | AST-based metrics + LLM semantic analysis, risk scoring |
| **Refactor** | Intelligent refactoring | Automated code generation, patch creation, backward compatibility |
| **Verifier** | Validation & testing | Syntax checking, test execution, coverage analysis, regression detection |

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lxcoo/RepoSage.git
cd repo-sage

# Install dependencies
pip install -r requirements.txt

# Set your LLM API key
export OPENAI_API_KEY="sk-..."
# Or for other providers
export REPOSAGE_LLM_API_KEY="..."
```

### Basic Usage

```bash
# Analyze current directory
python -m repo_sage.main analyze .

# Analyze with auto-refactoring enabled
python -m repo_sage.main analyze /path/to/project --auto-refactor

# Use a specific model
python -m repo_sage.main analyze . --model gpt-4 --provider openai

# Limit analysis scope
python -m repo_sage.main analyze . --max-files 20
```

### Programmatic API

```python
from repo_sage.agents.explorer_agent import ExplorerAgent
from repo_sage.agents.auditor_agent import AuditorAgent
from repo_sage.llm.provider import get_provider

# Initialize LLM
llm = get_provider("openai", api_key="sk-...", model="gpt-4")

# Run exploration
explorer = ExplorerAgent("Explorer", llm)
explore_result = explorer.execute_task(...)

# Run audit
auditor = AuditorAgent("Auditor", llm)
audit_result = auditor.execute_task(...)
```

## 📊 What Gets Analyzed?

### Static Analysis (AST-based)
- Cyclomatic complexity per function
- Function length and parameter count
- Missing type hints and docstrings
- Import analysis

### LLM-Powered Semantic Analysis
- Architectural design smells
- Security vulnerabilities
- Performance anti-patterns
- Maintainability issues
- Specific, actionable refactoring recommendations

### Verification
- Syntax validation
- Unit test execution (pytest)
- Code coverage reporting
- Regression detection

## 🛠️ Configuration

All behavior is configurable via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOSAGE_LLM_PROVIDER` | `openai` | LLM provider (openai, anthropic) |
| `REPOSAGE_LLM_API_KEY` | — | API key |
| `REPOSAGE_LLM_MODEL` | `gpt-4` | Model identifier |
| `REPOSAGE_LLM_TEMPERATURE` | `0.2` | Generation temperature |
| `REPOSAGE_LLM_MAX_TOKENS` | `4096` | Max tokens per request |
| `REPOSAGE_MAX_FILE_SIZE_KB` | `500` | Skip files larger than this |
| `REPOSAGE_AUTO_APPLY_REFACTOR` | `False` | Auto-apply refactoring |
| `REPOSAGE_OUTPUT_DIR` | `./reports` | Report output directory |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v --cov=repo_sage

# Run with demo repository
pytest src/demo_repo/ -v
```

## 📈 Token Consumption & Scale

RepoSage is designed for real-world engineering workflows:

- **Per-file analysis**: ~2,000-5,000 tokens (static summary + deep LLM audit)
- **Refactoring generation**: ~3,000-8,000 tokens per file
- **Typical project** (50 files): ~250,000-500,000 tokens per full pipeline run
- **Daily CI integration**: Recommended for teams running nightly audits

## 🗺️ Roadmap

- [ ] Multi-language support (TypeScript, Go, Rust, Java)
- [ ] Custom rule engine for organization-specific standards
- [ ] Integration with GitHub Actions / GitLab CI
- [ ] PR comment automation
- [ ] Fine-tuned models for domain-specific codebases

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

[MIT](LICENSE)

---

*Built with 🦾 by developers who believe code quality should be autonomous.*
