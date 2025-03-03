# agents/__init__.py

from .requirements_agent import RequirementsAgent
from .documentation_agent import DocumentationAgent
from .test_cases_agent import TestCasesAgent
from .code_agent import CodeAgent
from .bug_agent import BugAgent
from .report_agent import ReportAgent

# Экспорт классов для удобного импорта
__all__ = [
    "RequirementsAgent",
    "DocumentationAgent",
    "TestCasesAgent",
    "CodeAgent",
    "BugAgent",
    "ReportAgent"
]