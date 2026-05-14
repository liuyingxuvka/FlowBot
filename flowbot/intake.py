"""Startup intake records for FlowBot."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .io import ensure_dir, project_relative, write_json, write_text


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    return "run-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_confirmed_intake(
    project_root: Path,
    *,
    work_request: str,
    background_agents: bool = True,
    run_id: str | None = None,
) -> dict[str, object]:
    """Create a confirmed FlowBot intake and run shell."""

    if not work_request.strip():
        raise ValueError("work_request cannot be empty")

    run_id = run_id or new_run_id()
    run_root = project_root / ".flowbot" / "runs" / run_id
    intake_dir = ensure_dir(run_root / "intake")
    recorded_at = utc_now()
    answers = {
        "background_agents": "allow" if background_agents else "single-agent",
        "provenance": "explicit_user_reply",
    }

    body_path = write_text(intake_dir / "flowbot_intake_body.md", work_request.strip() + "\n")
    body_hash = sha256_text(work_request.strip() + "\n")
    receipt_path = intake_dir / "flowbot_intake_receipt.json"
    envelope_path = intake_dir / "flowbot_intake_envelope.json"
    result_path = intake_dir / "flowbot_intake_result.json"

    receipt = {
        "schema_version": "flowbot.intake_receipt.v1",
        "status": "confirmed",
        "ui_surface": "flowbot_startup_intake",
        "startup_answers": answers,
        "confirmed_by_user": True,
        "cancelled_by_user": False,
        "body_path": project_relative(project_root, body_path),
        "body_hash": body_hash,
        "envelope_path": project_relative(project_root, envelope_path),
        "body_text_included": False,
        "recorded_at": recorded_at,
    }
    write_json(receipt_path, receipt)

    envelope = {
        "schema_version": "flowbot.intake_envelope.v1",
        "status": "confirmed",
        "source": "flowbot_startup_intake",
        "startup_answers": answers,
        "body_path": project_relative(project_root, body_path),
        "body_hash": body_hash,
        "receipt_path": project_relative(project_root, receipt_path),
        "body_visibility": "sealed_pm_only",
        "controller_visibility": "envelope_only",
        "controller_may_read_body": False,
        "body_text_included": False,
        "recorded_at": recorded_at,
    }
    write_json(envelope_path, envelope)

    result = {
        "schema_version": "flowbot.intake_result.v1",
        "status": "confirmed",
        "run_id": run_id,
        "startup_answers": answers,
        "receipt_path": project_relative(project_root, receipt_path),
        "envelope_path": project_relative(project_root, envelope_path),
        "body_path": project_relative(project_root, body_path),
        "body_hash": body_hash,
        "controller_visibility": "envelope_only",
        "controller_may_read_body": False,
        "body_text_included": False,
        "recorded_at": recorded_at,
    }
    write_json(result_path, result)
    return {"run_id": run_id, "run_root": run_root, "result": result}


def create_cancelled_intake(project_root: Path) -> dict[str, object]:
    """Record a cancelled startup without creating a run."""

    cancelled_dir = ensure_dir(project_root / ".flowbot" / "cancelled_intake")
    result_path = cancelled_dir / f"cancelled-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    result = {
        "schema_version": "flowbot.intake_result.v1",
        "status": "cancelled",
        "controller_visibility": "cancel_status_only",
        "body_text_included": False,
        "recorded_at": utc_now(),
    }
    write_json(result_path, result)
    return {"result_path": result_path, "result": result}
