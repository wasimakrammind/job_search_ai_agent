"""
logger.py — Centralized decision logging for the Job Agent.

Every pipeline step logs its decisions here. The log is:
  1. Printed to console (for dev)
  2. Stored in a buffer (for the Gradio "Agent Log" tab)
  3. Exportable as text (for the report appendix / agent trace)
"""

import logging
from datetime import datetime


# ── In-memory buffer ─────────────────────────────────────────────────────────
LOG_BUFFER: list[str] = []


class _BufferHandler(logging.Handler):
    """Pushes formatted log lines into LOG_BUFFER."""
    def emit(self, record):
        LOG_BUFFER.append(self.format(record))


# ── Configure logger ─────────────────────────────────────────────────────────
logger = logging.getLogger("JobAgent")
logger.setLevel(logging.DEBUG)

_fmt = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

# Buffer handler (for UI)
_bh = _BufferHandler()
_bh.setFormatter(_fmt)
logger.addHandler(_bh)

# Console handler (for terminal / Colab output)
_sh = logging.StreamHandler()
_sh.setFormatter(_fmt)
logger.addHandler(_sh)


# ── Helper functions (used by Gradio UI) ─────────────────────────────────────
def get_logs(last_n: int = 300) -> str:
    """Return the last N log lines as a single string."""
    return "\n".join(LOG_BUFFER[-last_n:])


def clear_logs() -> str:
    """Wipe the log buffer. Returns empty string for Gradio output."""
    LOG_BUFFER.clear()
    return ""


def export_log() -> str:
    """Full log dump with header — paste into report appendix."""
    header = (
        f"{'='*70}\n"
        f"  AGENT TRACE LOG — Middle America Job Agent\n"
        f"  Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Total entries: {len(LOG_BUFFER)}\n"
        f"{'='*70}\n\n"
    )
    return header + "\n".join(LOG_BUFFER)
