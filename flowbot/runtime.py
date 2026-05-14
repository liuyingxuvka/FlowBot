"""Minimal FlowBot Router runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agents import ProjectManager, Worker
from .controller import Controller
from .intake import create_confirmed_intake, utc_now
from .io import ensure_dir, project_relative, read_json, read_text, write_json
from .mermaid import render_mermaid


REQUIRED_ROUTE_ARTIFACTS = {
    "user_contract",
    "route_hypothesis",
    "flowguard_route_model",
    "model_findings",
    "route_topology",
    "linear_route",
    "node_acceptance_contracts",
}


class FlowBotRuntime:
    """Router-owned execution loop for the FlowBot MVP demo."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def run(self, work_request: str, *, background_agents: bool = True) -> dict[str, Any]:
        intake = create_confirmed_intake(
            self.project_root,
            work_request=work_request,
            background_agents=background_agents,
        )
        return self.run_from_intake(intake)

    def run_from_intake_result(self, intake_result_path: Path) -> dict[str, Any]:
        result_path = intake_result_path.resolve()
        result = read_json(result_path)
        if result.get("status") != "confirmed":
            raise ValueError("FlowBot runtime requires a confirmed intake result")
        run_id = str(result.get("run_id") or "")
        if not run_id:
            raise ValueError("confirmed intake result is missing run_id")
        run_root = self.project_root / ".flowbot" / "runs" / run_id
        return self.run_from_intake({"run_id": run_id, "run_root": run_root, "result": result})

    def run_from_intake(self, intake: dict[str, Any]) -> dict[str, Any]:
        run_root = Path(intake["run_root"])
        for rel in ("letters", "checkins", "reviews", "artifacts"):
            ensure_dir(run_root / rel)

        state: dict[str, Any] = {
            "schema_version": "flowbot.router_state.v1",
            "run_id": intake["run_id"],
            "status": "RUN_CREATED",
            "current_node_id": None,
            "passed_node_ids": [],
            "retry_counts": {},
            "events": [{"event": "run_created", "recorded_at": utc_now()}],
        }
        self._save_state(run_root, state)

        controller = Controller(self.project_root, run_root)
        roles = controller.start_roles()
        state["status"] = "ROLES_READY"
        state["roles"] = roles
        state["events"].append({"event": "roles_ready", "recorded_at": utc_now()})
        self._save_state(run_root, state)

        pm = ProjectManager(self.project_root, run_root)
        worker = Worker(self.project_root, run_root)
        route_request = self._route_model_request(run_root, intake["result"])
        route_package = controller.deliver_to_pm(route_request, pm.synthesize_route)
        self._accept_route_package(run_root, state, route_package)

        work_request_body = read_text(self.project_root / str(intake["result"]["body_path"])).strip()
        for node in state["linear_route"]:
            state["current_node_id"] = node["id"]
            state["status"] = "NODE_DISPATCHED"
            work_letter = self._work_letter(run_root, state, node, work_request_body)
            checkin = controller.deliver_to_worker(work_letter, worker.execute)
            state["status"] = "WORKER_SUBMITTED"
            self._save_state(run_root, state)

            review_request = {
                "type": "review_request",
                "id": f"review-{node['id']}",
                "node": node,
                "checkin": checkin,
            }
            review = controller.deliver_to_pm(review_request, pm.review)
            if review["conclusion"] == "pass":
                state["passed_node_ids"].append(node["id"])
                state["status"] = "NODE_PASSED"
                state["events"].append({"event": "node_passed", "node_id": node["id"], "recorded_at": utc_now()})
                self._save_state(run_root, state)
                render_mermaid(run_root, state)
                continue
            self._handle_reject(run_root, state, node, review)
            break

        if len(state["passed_node_ids"]) == len(state.get("linear_route", [])):
            final = pm.final_acceptance(state["passed_node_ids"])
            state["final_acceptance"] = final
            state["status"] = "DONE" if final["accepted"] else "PAUSED"
            state["current_node_id"] = None
            state["events"].append({"event": "run_done", "recorded_at": utc_now(), "accepted": final["accepted"]})
            self._save_state(run_root, state)
            render_mermaid(run_root, state)
        return {"run_id": intake["run_id"], "run_root": run_root, "state": state}

    def _route_model_request(self, run_root: Path, intake_result: dict[str, Any]) -> dict[str, Any]:
        envelope = {
            "type": "route_model_request",
            "id": "route-model-request",
            "body_path": intake_result["body_path"],
            "body_hash": intake_result["body_hash"],
            "controller_may_read_body": False,
            "required_outputs": sorted(REQUIRED_ROUTE_ARTIFACTS),
        }
        write_json(run_root / "letters" / "route_model_request.json", envelope)
        return envelope

    def _accept_route_package(self, run_root: Path, state: dict[str, Any], package: dict[str, Any]) -> None:
        artifacts = set((package.get("artifacts") or {}).keys())
        missing = sorted(REQUIRED_ROUTE_ARTIFACTS - artifacts)
        if missing:
            raise RuntimeError(f"route package missing artifacts: {', '.join(missing)}")
        if not package.get("flowguard_result", {}).get("ok"):
            raise RuntimeError("route package FlowGuard result is not ok")
        route = package.get("linear_route") or []
        if not route:
            raise RuntimeError("route package has no linear route")
        state["status"] = "ROUTE_ACCEPTED"
        state["route_package_path"] = package.get("path")
        state["linear_route"] = route
        state["events"].append({"event": "route_accepted", "node_count": len(route), "recorded_at": utc_now()})
        self._save_state(run_root, state)
        render_mermaid(run_root, state)

    def _work_letter(self, run_root: Path, state: dict[str, Any], node: dict[str, Any], work_request: str) -> dict[str, Any]:
        letter = {
            "type": "work_letter",
            "schema_version": "flowbot.work_letter.v1",
            "id": f"work-{node['id']}",
            "node": node,
            "work_request": work_request,
            "scope": "current_node_only",
            "forbidden": ["do not change route", "do not process other nodes"],
            "completion_criteria": node["acceptance"],
            "evidence_required": node["acceptance"],
            "created_at": utc_now(),
        }
        write_json(run_root / "letters" / f"{node['id']}_work_letter.json", letter)
        state["events"].append({"event": "work_letter_created", "node_id": node["id"], "recorded_at": utc_now()})
        self._save_state(run_root, state)
        render_mermaid(run_root, state)
        return letter

    def _handle_reject(self, run_root: Path, state: dict[str, Any], node: dict[str, Any], review: dict[str, Any]) -> None:
        count = int(state["retry_counts"].get(node["id"], 0)) + 1
        state["retry_counts"][node["id"]] = count
        if count > 2:
            state["status"] = "PAUSED"
            state["pause_reason"] = f"retry limit reached for {node['id']}"
        else:
            state["status"] = "NODE_RETRYING"
            repair = {
                "type": "repair_letter",
                "schema_version": "flowbot.repair_letter.v1",
                "node": node,
                "review": review,
                "created_at": utc_now(),
            }
            write_json(run_root / "letters" / f"{node['id']}_repair_letter.json", repair)
        self._save_state(run_root, state)
        render_mermaid(run_root, state)

    def _save_state(self, run_root: Path, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        write_json(run_root / "router_state.json", state)
