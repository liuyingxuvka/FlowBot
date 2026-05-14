"""Mermaid progress rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import write_text


def render_mermaid(run_root: Path, state: dict[str, Any]) -> Path:
    route = state.get("linear_route") or []
    current = state.get("current_node_id")
    passed = set(state.get("passed_node_ids") or [])
    status = state.get("status", "unknown")

    lines = ["flowchart TD", "    A[FlowBot run] --> B[PM FlowGuard route model]"]
    previous = "B"
    for idx, node in enumerate(route, start=1):
        node_id = node["id"]
        label = node.get("title") or node_id
        marker = ""
        if node_id in passed:
            marker = " passed"
        elif node_id == current:
            marker = " current"
        graph_id = f"N{idx}"
        lines.append(f"    {previous} --> {graph_id}[{label}{marker}]")
        previous = graph_id
    lines.append(f"    {previous} --> Z[Status: {status}]")
    return write_text(run_root / "mermaid.mmd", "```mermaid\n" + "\n".join(lines) + "\n```\n")
