# utils/audit_trail.py
"""
Self-contained audit trail so we can see exactly what happened during a run
without depending on Streamlit Cloud's "Manage app" logs (which aren't
always available/visible to us).

Every step is recorded to:
  1. An in-memory list for the current process (fast, shown in the UI).
  2. An append-only JSONL file (audit_trail.log) so it survives Streamlit
     reruns within the same deployed container.

Import this module first, before anything else that might fail, so even an
import-time crash gets a chance to be logged and shown on-screen.
"""
import json
import os
import time
import traceback

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_trail.log")
_MAX_MEMORY_ENTRIES = 500

_entries = []


def log_step(stage, status, detail=None, error=None):
    """
    stage: short name of the step, e.g. "import", "agent:hotel", "gemini:tour:tours"
    status: "start" | "success" | "error"
    detail: optional short human-readable string
    error: optional exception — its full traceback is captured automatically
    """
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stage": stage,
        "status": status,
    }
    if detail:
        entry["detail"] = str(detail)
    if error is not None:
        entry["error"] = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    _entries.append(entry)
    if len(_entries) > _MAX_MEMORY_ENTRIES:
        del _entries[0]

    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # audit logging must never itself crash the app

    return entry


def step(stage):
    """Context manager: logs start/success/error around a block of code."""
    return _StepContext(stage)


class _StepContext:
    def __init__(self, stage):
        self.stage = stage

    def __enter__(self):
        log_step(self.stage, "start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            log_step(self.stage, "error", error=exc_val)
        else:
            log_step(self.stage, "success")
        return False  # never swallow the exception


def get_recent_entries(limit=200):
    """In-memory entries for the current process, most recent last."""
    return _entries[-limit:]


def get_log_file_text(max_chars=50000):
    """Full persisted log (across reruns), tail-truncated to max_chars."""
    try:
        with open(_LOG_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        return text[-max_chars:]
    except FileNotFoundError:
        return "(no audit log written yet)"
    except Exception as e:
        return f"(failed to read audit log: {e!r})"


def format_entries_as_text(entries):
    lines = []
    for e in entries:
        line = f"[{e['ts']}] {e['stage']} — {e['status']}"
        if e.get("detail"):
            line += f" — {e['detail']}"
        lines.append(line)
        if e.get("error"):
            lines.append(e["error"])
    return "\n".join(lines)
