"""Run FlowBot from a confirmed startup intake result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flowbot.runtime import FlowBotRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--intake-result", required=True)
    args = parser.parse_args()

    runtime = FlowBotRuntime(Path(args.project_root).resolve())
    result = runtime.run_from_intake_result(Path(args.intake_result))
    payload = {
        "run_id": result["run_id"],
        "run_root": str(result["run_root"]),
        "status": result["state"]["status"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
