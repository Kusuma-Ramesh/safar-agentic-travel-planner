"""A small log of tool calls so the UI can show how a plan was produced."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Trace:
    steps: list[dict] = field(default_factory=list)

    def record(self, tool: str, inputs: dict, summary: str, started: float | None = None) -> None:
        elapsed = int((time.perf_counter() - started) * 1000) if started else None
        self.steps.append({"tool": tool, "inputs": inputs, "summary": summary, "ms": elapsed})
