"""Deterministic PM and Worker agents for the FlowBot MVP demo."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from flowbot_models import route_synthesis_model

from .intake import utc_now
from .io import ensure_dir, project_relative, read_text, write_json, write_text


class ProjectManager:
    """PM owns route synthesis and evidence review."""

    def __init__(self, project_root: Path, run_root: Path) -> None:
        self.project_root = project_root
        self.run_root = run_root
        self.pm_root = ensure_dir(run_root / "pm")

    def synthesize_route(self, envelope: dict[str, Any]) -> dict[str, Any]:
        body_path = self.project_root / str(envelope["body_path"])
        work_request = read_text(body_path).strip()
        result = route_synthesis_model.run_checks()
        if not result["ok"]:
            raise RuntimeError("FlowGuard route synthesis model failed")

        user_contract_path = write_text(
            self.pm_root / "user_contract.md",
            "# User Contract\n\n"
            f"Original request:\n\n{work_request}\n\n"
            "Completion means the demo run produces a note, a summary, and a final report with evidence.\n",
        )
        route_hypothesis_path = write_text(
            self.pm_root / "route_hypothesis.md",
            "# Route Hypothesis\n\n"
            "Capture the request, summarize it, then produce a final report. "
            "The route is intentionally linear for the FlowBot MVP demo.\n",
        )
        model_path = write_text(
            self.pm_root / "flowguard_route_model.py",
            inspect.getsource(route_synthesis_model),
        )
        findings_path = write_text(
            self.pm_root / "model_findings.md",
            "# Model Findings\n\n"
            f"- FlowGuard summary: {result['flowguard']['summary']}\n"
            f"- Violations: {result['flowguard']['violation_count']}\n"
            f"- Hazard checks detected: {sum(1 for h in result['hazards'].values() if h['detected'])}\n",
        )
        linear_route = result["linear_route"]
        topology = {
            "schema_version": "flowbot.route_topology.v1",
            "source": "flowguard_route_model",
            "start": linear_route[0]["id"],
            "done": "done",
            "nodes": linear_route,
            "edges": [
                {"from": linear_route[idx]["id"], "to": linear_route[idx + 1]["id"]}
                for idx in range(len(linear_route) - 1)
            ]
            + [{"from": linear_route[-1]["id"], "to": "done"}],
        }
        topology_path = write_json(self.pm_root / "route_topology.json", topology)
        linear_route_path = write_json(
            self.pm_root / "linear_route.json",
            {"schema_version": "flowbot.linear_route.v1", "nodes": linear_route},
        )
        acceptance = {
            node["id"]: {"acceptance": node["acceptance"], "worker_action": node["worker_action"]}
            for node in linear_route
        }
        acceptance_path = write_json(
            self.pm_root / "node_acceptance_contracts.json",
            {"schema_version": "flowbot.node_acceptance_contracts.v1", "contracts": acceptance},
        )
        flowguard_result_path = write_json(self.pm_root / "flowguard_result.json", result)

        package = {
            "type": "route_package",
            "schema_version": "flowbot.route_package.v1",
            "created_by": "pm",
            "created_at": utc_now(),
            "flowguard_result": {"ok": True, "path": project_relative(self.project_root, flowguard_result_path)},
            "artifacts": {
                "user_contract": project_relative(self.project_root, user_contract_path),
                "route_hypothesis": project_relative(self.project_root, route_hypothesis_path),
                "flowguard_route_model": project_relative(self.project_root, model_path),
                "model_findings": project_relative(self.project_root, findings_path),
                "route_topology": project_relative(self.project_root, topology_path),
                "linear_route": project_relative(self.project_root, linear_route_path),
                "node_acceptance_contracts": project_relative(self.project_root, acceptance_path),
            },
            "linear_route": linear_route,
        }
        package_path = write_json(self.pm_root / "route_package.json", package)
        package["path"] = project_relative(self.project_root, package_path)
        write_json(package_path, package)
        return package

    def review(self, envelope: dict[str, Any]) -> dict[str, Any]:
        node = envelope["node"]
        checkin = envelope["checkin"]
        missing = []
        for rel in checkin.get("evidence_paths", []):
            if not (self.run_root / rel).exists():
                missing.append(rel)
        conclusion = "pass" if not missing else "reject"
        review = {
            "type": "pm_review",
            "schema_version": "flowbot.pm_review.v1",
            "node_id": node["id"],
            "conclusion": conclusion,
            "evidence_checked": checkin.get("evidence_paths", []),
            "issues": [f"Missing evidence: {path}" for path in missing],
            "repair_instruction": "" if conclusion == "pass" else "Regenerate only the missing evidence for this node.",
            "reviewed_at": utc_now(),
        }
        write_json(self.run_root / "reviews" / f"{node['id']}_pm_review.json", review)
        return review

    def final_acceptance(self, passed_node_ids: list[str]) -> dict[str, Any]:
        final_report = self.run_root / "artifacts" / "final_report.md"
        accepted = final_report.exists() and len(passed_node_ids) == len(route_synthesis_model.DEMO_LINEAR_ROUTE)
        payload = {
            "schema_version": "flowbot.final_acceptance.v1",
            "accepted": accepted,
            "passed_node_ids": passed_node_ids,
            "final_report": project_relative(self.project_root, final_report) if final_report.exists() else None,
            "reviewed_at": utc_now(),
        }
        write_json(self.pm_root / "final_acceptance.json", payload)
        return payload


class Worker:
    """Worker executes only the current work letter."""

    def __init__(self, project_root: Path, run_root: Path) -> None:
        self.project_root = project_root
        self.run_root = run_root
        self.artifacts = ensure_dir(run_root / "artifacts")

    def execute(self, envelope: dict[str, Any]) -> dict[str, Any]:
        node = envelope["node"]
        action = node["worker_action"]
        evidence_paths: list[str] = []
        if action == "write_note":
            target = write_text(self.artifacts / "note.md", "# Note\n\n" + envelope["work_request"] + "\n")
            evidence_paths.append(project_relative(self.run_root, target))
        elif action == "write_summary":
            note = self.artifacts / "note.md"
            target = write_text(
                self.artifacts / "summary.md",
                "# Summary\n\n"
                f"Based on `{project_relative(self.run_root, note)}`, this demo captures the request and prepares a final report.\n",
            )
            evidence_paths.append(project_relative(self.run_root, target))
        elif action == "write_final_report":
            summary = self.artifacts / "summary.md"
            target = write_text(
                self.artifacts / "final_report.md",
                "# Final Report\n\n"
                f"FlowBot demo completed the linear route and reviewed evidence from `{project_relative(self.run_root, summary)}`.\n",
            )
            evidence_paths.append(project_relative(self.run_root, target))
        else:
            raise ValueError(f"unknown worker action: {action}")

        checkin = {
            "type": "worker_checkin",
            "schema_version": "flowbot.worker_checkin.v1",
            "node_id": node["id"],
            "status": "submitted",
            "completed_action": action,
            "evidence_paths": evidence_paths,
            "submitted_at": utc_now(),
        }
        write_json(self.run_root / "checkins" / f"{node['id']}_worker_checkin.json", checkin)
        return checkin
