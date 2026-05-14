"""Relay-only Controller for FlowBot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .intake import utc_now
from .io import read_json, write_json


class Controller:
    """Controller creates/connects roles and relays Router-authorized envelopes."""

    def __init__(self, project_root: Path, run_root: Path) -> None:
        self.project_root = project_root
        self.run_root = run_root
        self.ledger_path = run_root / "controller_ledger.json"
        if not self.ledger_path.exists():
            write_json(
                self.ledger_path,
                {
                    "schema_version": "flowbot.controller_ledger.v1",
                    "entries": [],
                    "controller_role": "relay_only",
                },
            )

    def _append(self, entry: dict[str, Any]) -> None:
        ledger = read_json(self.ledger_path)
        ledger.setdefault("entries", []).append({"recorded_at": utc_now(), **entry})
        write_json(self.ledger_path, ledger)

    def start_roles(self) -> dict[str, Any]:
        result = {
            "schema_version": "flowbot.roles_ready.v1",
            "pm_ready": True,
            "worker_ready": True,
            "controller_may_plan": False,
            "controller_may_execute": False,
            "controller_may_review": False,
        }
        self._append({"event": "roles_ready", "result": result})
        return result

    def deliver_to_pm(self, envelope: dict[str, Any], handler: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        self._append({"event": "deliver_to_pm", "envelope_type": envelope.get("type"), "envelope_id": envelope.get("id")})
        result = handler(envelope)
        self._append({"event": "return_from_pm", "envelope_type": envelope.get("type"), "result_type": result.get("type")})
        return result

    def deliver_to_worker(self, envelope: dict[str, Any], handler: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        self._append({"event": "deliver_to_worker", "envelope_type": envelope.get("type"), "envelope_id": envelope.get("id")})
        result = handler(envelope)
        self._append({"event": "return_from_worker", "envelope_type": envelope.get("type"), "result_type": result.get("type")})
        return result
