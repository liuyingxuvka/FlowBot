"""FlowBot demo entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .runtime import FlowBotRuntime


DEFAULT_REQUEST = "Use FlowBot to run a tiny demo: capture this request, summarize it, and write a final report."


def run_demo(project_root: Path, request: str = DEFAULT_REQUEST) -> dict[str, object]:
    runtime = FlowBotRuntime(project_root)
    return runtime.run(request, background_agents=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    result = run_demo(Path(args.project_root).resolve(), args.request)
    print(f"FlowBot demo completed: {result['run_id']}")
    print(f"Run root: {result['run_root']}")
    print(f"Status: {result['state']['status']}")
    return 0 if result["state"]["status"] == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
