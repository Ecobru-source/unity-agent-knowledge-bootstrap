#!/usr/bin/env python3
"""Scaffold a Unity project's local agent knowledge base."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scan_unity_project import is_unity_project, validation_messages  # noqa: E402

SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"

AGENTS_BEGIN = "<!-- BEGIN UNITY AGENT KNOWLEDGE -->"
AGENTS_END = "<!-- END UNITY AGENT KNOWLEDGE -->"
RG_BEGIN = "# BEGIN UNITY AGENT KNOWLEDGE IGNORE"
RG_END = "# END UNITY AGENT KNOWLEDGE IGNORE"

KNOWLEDGE_DIRS = [
    "raw/scans",
    "raw/notes",
    "raw/assets",
    "entities",
    "concepts",
    "comparisons",
    "queries",
    "decisions",
    "templates",
]


def today() -> str:
    return dt.date.today().isoformat()


def read_template(relative_path: str) -> str:
    return (TEMPLATE_DIR / relative_path).read_text(encoding="utf-8")


def write_text(path: Path, text: str, dry_run: bool) -> None:
    if dry_run:
        print(f"Would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def upsert_marked_block(path: Path, begin: str, end: str, block_body: str, header: str | None, dry_run: bool) -> str:
    block = f"{begin}\n{block_body.rstrip()}\n{end}"
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = (header.rstrip() + "\n\n") if header else ""
    if begin in text and end in text:
        text = re.sub(re.escape(begin) + r".*?" + re.escape(end), block, text, flags=re.DOTALL)
        action = "updated"
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
        action = "created" if not path.exists() else "updated"
    write_text(path, text, dry_run)
    return action


def materialize_template(src_relative: str, dest: Path, dry_run: bool, overwrite: bool = False) -> str:
    existed = dest.exists()
    if dest.exists() and not overwrite:
        return "skipped"
    text = read_template(src_relative)
    text = text.replace("YYYY-MM-DD", today())
    write_text(dest, text, dry_run)
    return "updated" if existed else "created"


def append_log(knowledge: Path, created: list[str], updated: list[str], dry_run: bool) -> None:
    lines = [
        "",
        f"## [{today()}] scaffold | Agent knowledge initialized",
    ]
    if created:
        lines.append("- Created:")
        lines.extend(f"  - `{item}`" for item in created)
    if updated:
        lines.append("- Updated:")
        lines.extend(f"  - `{item}`" for item in updated)
    if dry_run:
        print(f"Would append scaffold log to {knowledge / 'log.md'}")
        return
    with (knowledge / "log.md").open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def scaffold(project: Path, knowledge_relative: str, dry_run: bool, no_refresh: bool) -> int:
    if not is_unity_project(project):
        print("Not a Unity project. No files were written.")
        for message in validation_messages(project):
            print(f"- {message}")
        return 2

    knowledge = project / knowledge_relative
    created: list[str] = []
    updated: list[str] = []

    for rel_dir in KNOWLEDGE_DIRS:
        path = knowledge / rel_dir
        if path.exists():
            continue
        if dry_run:
            print(f"Would create directory {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
        created.append(path.relative_to(project).as_posix() + "/")

    agents_action = upsert_marked_block(
        project / "AGENTS.md",
        AGENTS_BEGIN,
        AGENTS_END,
        read_template("AGENTS.block.md"),
        "# AGENTS.md",
        dry_run,
    )
    (created if agents_action == "created" else updated).append("AGENTS.md")

    rg_action = upsert_marked_block(
        project / ".rgignore",
        RG_BEGIN,
        RG_END,
        read_template("rgignore.template"),
        None,
        dry_run,
    )
    (created if rg_action == "created" else updated).append(".rgignore")

    template_map = {
        "AgentKnowledge/SCHEMA.md": knowledge / "SCHEMA.md",
        "AgentKnowledge/index.md": knowledge / "index.md",
        "AgentKnowledge/log.md": knowledge / "log.md",
        "AgentKnowledge/home.md": knowledge / "home.md",
        "AgentKnowledge/templates/entity.md": knowledge / "templates" / "entity.md",
        "AgentKnowledge/templates/concept.md": knowledge / "templates" / "concept.md",
        "AgentKnowledge/templates/query.md": knowledge / "templates" / "query.md",
        "AgentKnowledge/templates/decision.md": knowledge / "templates" / "decision.md",
    }
    for src, dest in template_map.items():
        status = materialize_template(src, dest, dry_run)
        if status == "created":
            created.append(dest.relative_to(project).as_posix())
        elif status == "updated":
            updated.append(dest.relative_to(project).as_posix())

    append_log(knowledge, created, updated, dry_run)

    if not no_refresh:
        refresh_script = SCRIPT_DIR / "refresh_unity_agent_knowledge.py"
        cmd = [
            sys.executable,
            str(refresh_script),
            "--project",
            str(project),
            "--knowledge-dir",
            knowledge_relative,
        ]
        if dry_run:
            cmd.append("--dry-run")
        result = subprocess.run(cmd, check=False)
        return result.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a Unity agent knowledge base.")
    parser.add_argument("--project", default=".", help="Unity project root.")
    parser.add_argument("--knowledge-dir", default="Docs/AgentKnowledge", help="Knowledge directory relative to project root.")
    parser.add_argument("--dry-run", action="store_true", help="Print intended writes without modifying files.")
    parser.add_argument("--no-refresh", action="store_true", help="Skip initial roadmap refresh.")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    return scaffold(project, args.knowledge_dir, args.dry_run, args.no_refresh)


if __name__ == "__main__":
    raise SystemExit(main())
