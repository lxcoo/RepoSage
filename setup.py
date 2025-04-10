from setuptools import setup, find_packages

setup(
    name="repo-sage",
    version="0.1.0",
    description="Multi-Agent Intelligent Codebase Governance System",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai>=1.0.0",
        "pytest>=7.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "repo-sage=repo_sage.main:app",
        ],
    },
)
