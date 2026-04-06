"""
Centralized configuration for the Darwin Godel Machine.

All tunable parameters are gathered here so the system can be steered toward
different goals (e.g. aggressive exploration vs. exploitation, different model
families, budget caps) without editing multiple source files.
"""

import os

# ── LLM Model Configuration ──────────────────────────────────────────────────

CODING_AGENT_MODEL = os.getenv(
    "DGM_CODING_MODEL",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
)

DIAGNOSE_MODEL = os.getenv("DGM_DIAGNOSE_MODEL", "o1-2024-12-17")

TIEBREAKER_MODEL = os.getenv("DGM_TIEBREAKER_MODEL", "o1-2024-12-17")

# ── Token / Context Limits ───────────────────────────────────────────────────

MAX_OUTPUT_TOKENS = int(os.getenv("DGM_MAX_OUTPUT_TOKENS", "4096"))

TOOL_OUTPUT_MAX_CHARS = int(os.getenv("DGM_TOOL_OUTPUT_MAX_CHARS", "40000"))

# ── Timeouts (seconds) ───────────────────────────────────────────────────────

SELF_IMPROVE_TIMEOUT = int(os.getenv("DGM_SELF_IMPROVE_TIMEOUT", "1800"))

CODING_AGENT_TIMEOUT = int(os.getenv("DGM_CODING_AGENT_TIMEOUT", "32400"))

BASH_TOOL_TIMEOUT = float(os.getenv("DGM_BASH_TOOL_TIMEOUT", "120.0"))

# ── Evolutionary Parameters ──────────────────────────────────────────────────

CONVERGENCE_WINDOW = int(os.getenv("DGM_CONVERGENCE_WINDOW", "5"))

CONVERGENCE_THRESHOLD = float(os.getenv("DGM_CONVERGENCE_THRESHOLD", "0.005"))

MIN_ARCHIVE_SCORE = float(os.getenv("DGM_MIN_ARCHIVE_SCORE", "0.4"))

# ── Reproducibility ──────────────────────────────────────────────────────────

RANDOM_SEED = os.getenv("DGM_RANDOM_SEED", None)
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)
