"""Focused smoke checks for the FlowBot MVP runtime."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flowbot.demo import run_demo
from flowbot.intake import create_cancelled_intake
from flowbot.runtime import FlowBotRuntime


def _clean_smoke_root() -> Path:
    root = ROOT / "tmp" / "flowbot_smoke"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_checks() -> dict[str, object]:
    smoke_root = _clean_smoke_root()
    checks: dict[str, object] = {}

    cancel = create_cancelled_intake(smoke_root)
    checks["cancel_before_run"] = {
        "ok": cancel["result"]["status"] == "cancelled" and not (smoke_root / ".flowbot" / "runs").exists(),
        "result_path": str(cancel["result_path"]),
    }

    demo = run_demo(smoke_root, "Use FlowBot smoke check to create a note, summary, and final report.")
    run_root = Path(demo["run_root"])
    state = demo["state"]
    route_package = _read_json(run_root / "pm" / "route_package.json")
    ledger = _read_json(run_root / "controller_ledger.json")
    checks["demo_done"] = {
        "ok": state["status"] == "DONE",
        "run_root": str(run_root),
    }
    checks["route_package_model_backed"] = {
        "ok": bool(route_package.get("flowguard_result", {}).get("ok"))
        and all(
            key in route_package.get("artifacts", {})
            for key in (
                "user_contract",
                "route_hypothesis",
                "flowguard_route_model",
                "model_findings",
                "route_topology",
                "linear_route",
                "node_acceptance_contracts",
            )
        ),
    }
    checks["controller_relay_only"] = {
        "ok": any(entry.get("event") == "roles_ready" for entry in ledger.get("entries", []))
        and all(entry.get("event") not in {"controller_planned", "controller_executed", "controller_reviewed"} for entry in ledger.get("entries", [])),
    }
    checks["evidence_complete"] = {
        "ok": all(
            (run_root / rel).exists()
            for rel in (
                "artifacts/note.md",
                "artifacts/summary.md",
                "artifacts/final_report.md",
                "pm/final_acceptance.json",
                "mermaid.mmd",
            )
        )
    }

    runtime = FlowBotRuntime(smoke_root)
    rejection_state = {"events": [], "status": "RUN_CREATED"}
    try:
        runtime._accept_route_package(  # noqa: SLF001 - focused boundary smoke.
            smoke_root,
            rejection_state,
            {"flowguard_result": {"ok": True}, "artifacts": {}, "linear_route": []},
        )
        rejected_missing_route_artifacts = False
    except RuntimeError:
        rejected_missing_route_artifacts = True
    checks["missing_route_artifacts_rejected"] = {"ok": rejected_missing_route_artifacts}

    ok = all(bool(item.get("ok")) for item in checks.values() if isinstance(item, dict))
    return {"ok": ok, "checks": checks}


def main() -> int:
    report = run_checks()
    output = ROOT / "tmp" / "flowbot_smoke_results.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
