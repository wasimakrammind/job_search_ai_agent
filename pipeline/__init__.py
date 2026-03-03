"""
pipeline/ — Core agent pipeline modules.

Each module = one pipeline stage = one team member's ownership.

    search.py   → Web Engineer
    filter.py   → Agent Architect
    rank.py     → LLM Engineer
    tailor.py   → LLM Engineer
    evaluate.py → Eval Lead
"""

from .search import run_search
from .filter import run_filter
from .rank import run_rank
from .tailor import run_tailor
from .evaluate import run_evaluation
from .ethics import run_ethics_analysis

__all__ = ["run_search", "run_filter", "run_rank", "run_tailor", "run_evaluation", "run_ethics_analysis"]