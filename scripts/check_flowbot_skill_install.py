"""Verify the local FlowBot Codex skill installation."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "flowbot"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PLACEHOLDER = "<FLOWBOT_REPO>"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def main() -> int:
    source = ROOT / "skills" / SKILL_NAME / "SKILL.md"
    installed = codex_home() / "skills" / SKILL_NAME / "SKILL.md"
    rendered_source = ""
    report = {
        "ok": False,
        "source": str(source),
        "installed": str(installed),
        "checks": {
            "source_exists": source.exists(),
            "installed_exists": installed.exists(),
            "source_has_name": False,
            "source_has_version": False,
            "source_is_public_safe": False,
            "installed_has_name": False,
            "installed_has_version": False,
            "installed_points_to_project": False,
            "installed_matches_rendered_source": False,
        },
    }
    if source.exists():
        source_text = source.read_text(encoding="utf-8")
        report["checks"]["source_has_name"] = "name: flowbot" in source_text
        report["checks"]["source_has_version"] = VERSION in source_text
        report["checks"]["source_is_public_safe"] = (
            PLACEHOLDER in source_text
            and "C:\\Users\\" not in source_text
            and "/Users/" not in source_text
        )
        rendered_source = source_text.replace(PLACEHOLDER, str(ROOT))
    if installed.exists():
        installed_text = installed.read_text(encoding="utf-8")
        report["checks"]["installed_has_name"] = "name: flowbot" in installed_text
        report["checks"]["installed_has_version"] = VERSION in installed_text
        report["checks"]["installed_points_to_project"] = str(ROOT) in installed_text
    if source.exists() and installed.exists():
        report["source_sha256"] = sha256(source)
        report["installed_sha256"] = sha256(installed)
        report["rendered_source_sha256"] = hashlib.sha256(rendered_source.encode("utf-8")).hexdigest()
        report["checks"]["installed_matches_rendered_source"] = rendered_source == installed_text

    required_checks = (
        "source_exists",
        "installed_exists",
        "source_has_name",
        "source_has_version",
        "source_is_public_safe",
        "installed_has_name",
        "installed_has_version",
        "installed_points_to_project",
        "installed_matches_rendered_source",
    )
    report["ok"] = all(report["checks"][name] for name in required_checks)
    output = ROOT / "tmp" / "flowbot_skill_install_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
