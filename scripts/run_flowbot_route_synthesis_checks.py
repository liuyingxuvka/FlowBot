"""Run FlowGuard checks for the FlowBot PM route synthesis model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flowbot_models.route_synthesis_model import run_checks


def main() -> int:
    report = run_checks()
    output = ROOT / "tmp" / "flowguard" / "flowbot_route_synthesis_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
