"""Install the FlowBot Codex skill from this checkout.

The repository source skill is public-safe and uses a <FLOWBOT_REPO>
placeholder. This installer renders that placeholder to the current checkout
path only in the user's local Codex skills directory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "flowbot"
PLACEHOLDER = "<FLOWBOT_REPO>"


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def render_skill() -> str:
    source = ROOT / "skills" / SKILL_NAME / "SKILL.md"
    text = source.read_text(encoding="utf-8")
    if PLACEHOLDER not in text:
        raise RuntimeError(f"{source} does not contain {PLACEHOLDER}")
    return text.replace(PLACEHOLDER, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Install FlowBot as a local Codex skill.")
    parser.add_argument("--check", action="store_true", help="Report whether the installed skill already matches.")
    args = parser.parse_args()

    source = ROOT / "skills" / SKILL_NAME / "SKILL.md"
    target = codex_home() / "skills" / SKILL_NAME / "SKILL.md"
    rendered = render_skill()
    installed_text = target.read_text(encoding="utf-8") if target.exists() else ""
    matches = installed_text == rendered
    report = {
        "ok": matches if args.check else True,
        "mode": "check" if args.check else "install",
        "source": str(source),
        "target": str(target),
        "matches": matches,
    }
    if not args.check:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        report["matches"] = True
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
