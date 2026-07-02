#!/usr/bin/env python3
"""Refresh generated Unity agent knowledge pages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scan_unity_project import is_unity_project, render_scan_markdown, scan_project, validation_messages  # noqa: E402


INDEX_BEGIN = "<!-- BEGIN GENERATED UNITY AGENT KNOWLEDGE INDEX -->"
INDEX_END = "<!-- END GENERATED UNITY AGENT KNOWLEDGE INDEX -->"


def today() -> str:
    return dt.date.today().isoformat()


def timestamp_slug() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")


def wiki_link(path: str) -> str:
    slug = Path(path).stem
    return f"[[{slug}]]"


def frontmatter(title: str, page_type: str, tags: list[str], confidence: str = "medium") -> str:
    tag_text = ", ".join(tags)
    date = today()
    return (
        "---\n"
        f"title: {title}\n"
        f"created: {date}\n"
        f"updated: {date}\n"
        f"type: {page_type}\n"
        f"tags: [{tag_text}]\n"
        "sources: []\n"
        f"confidence: {confidence}\n"
        "---\n\n"
    )


def write_page(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"Would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def append_log(knowledge: Path, action: str, subject: str, created: list[str], updated: list[str], dry_run: bool) -> None:
    lines = [
        "",
        f"## [{today()}] {action} | {subject}",
    ]
    if created:
        lines.append("- Created:")
        lines.extend(f"  - `{item}`" for item in created)
    if updated:
        lines.append("- Updated:")
        lines.extend(f"  - `{item}`" for item in updated)
    text = "\n".join(lines) + "\n"
    if dry_run:
        print(f"Would append log entry to {knowledge / 'log.md'}")
        return
    with (knowledge / "log.md").open("a", encoding="utf-8") as handle:
        handle.write(text)


def generated_notice() -> str:
    return (
        "> Generated from static project scan. Use this as a navigation aid. "
        "Verify task-relevant claims against source, scene, prefab, ScriptableObject, or config files before acting.\n"
    )


def render_home(scan: dict[str, Any]) -> str:
    return frontmatter("Agent Knowledge Home", "summary", ["unity", "project-map"]) + "\n".join(
        [
            "# Agent Knowledge Home",
            "",
            "Start here when working in this Unity project.",
            "",
            "## Read Order",
            "",
            "1. `AGENTS.md`",
            "2. `Docs/AgentKnowledge/project-map.md`",
            "3. `Docs/AgentKnowledge/code-roadmap.md`",
            "4. `Docs/AgentKnowledge/index.md`",
            "5. Task-relevant pages",
            "",
            "## Current Static Scan",
            "",
            f"- Unity project detected: `{scan['is_unity_project']}`",
            f"- C# files: {scan['counts']['csharp_files']}",
            f"- Inferred modules: {scan['counts']['modules']}",
            f"- Scenes: {scan['counts']['scenes']}",
            "",
            "## Ground Rules",
            "",
            "- Prefer targeted search over broad repository scans.",
            "- Treat generated roadmaps as navigation, not final truth.",
            "- Verify relevant files before making decisions.",
            "- Keep durable findings in this wiki and append `log.md`.",
        ]
    )


def render_project_map(scan: dict[str, Any]) -> str:
    counts = scan["counts"]
    body = [
        "# Project Map",
        "",
        generated_notice(),
        "## Project Markers",
        "",
        f"- Project root: `{scan['project_root']}`",
        f"- Unity project detected: `{scan['is_unity_project']}`",
        f"- Generated at: `{scan['generated_at']}`",
        "",
        "## Counts",
        "",
        f"- Files scanned: {counts['files_scanned']}",
        f"- C# files: {counts['csharp_files']}",
        f"- Inferred modules: {counts['modules']}",
        f"- Scenes: {counts['scenes']}",
        f"- Prefabs listed: {counts['prefabs']}",
        f"- Assembly definitions: {counts['asmdefs']}",
        f"- Config/data files listed: {counts['configs']}",
        f"- Packages: {counts['packages']}",
        "",
        "## Navigation",
        "",
        "- [[module-index]]",
        "- [[code-roadmap]]",
        "- [[scene-index]]",
        "- [[config-index]]",
        "",
        "## Validation",
        "",
    ]
    if scan["validation_messages"]:
        body.extend(f"- {message}" for message in scan["validation_messages"])
    else:
        body.append("- Unity project markers found.")
    return frontmatter("Project Map", "summary", ["unity", "project-map"]) + "\n".join(body)


def render_module_index(scan: dict[str, Any]) -> str:
    body = [
        "# Module Index",
        "",
        generated_notice(),
        "## Inferred Modules",
        "",
    ]
    if not scan["modules"]:
        body.append("- No C# modules inferred.")
    for name, module in scan["modules"].items():
        body.extend(
            [
                f"### {name}",
                "",
                f"- Files: {module['file_count']}",
                f"- Categories: `{module['categories']}`",
                f"- Classes: {', '.join(module['classes']) if module['classes'] else 'None detected'}",
                f"- Unity callbacks: {', '.join(module['callbacks']) if module['callbacks'] else 'None detected'}",
                "- Sample files:",
            ]
        )
        body.extend(f"  - `{path}`" for path in module["sample_files"])
        body.append("")
    return frontmatter("Module Index", "summary", ["unity", "module", "code-roadmap"]) + "\n".join(body)


def render_code_roadmap(scan: dict[str, Any]) -> str:
    body = [
        "# Code Roadmap",
        "",
        generated_notice(),
        "## How to Use",
        "",
        "- Use this page to find likely entry points quickly.",
        "- Do not treat module responsibilities as verified until task-specific source reads confirm them.",
        "- Upgrade related topic pages to `confidence: high` only after verification.",
        "",
        "## Roadmap",
        "",
    ]
    if not scan["modules"]:
        body.append("- No C# code was found in scanned Unity paths.")
    for name, module in scan["modules"].items():
        body.extend(
            [
                f"### {name}",
                "",
                "confidence: medium",
                "",
                "Primary files:",
            ]
        )
        body.extend(f"- `{path}`" for path in module["sample_files"][:8])
        body.extend(
            [
                "",
                "Likely entry points:",
            ]
        )
        callbacks = module["callbacks"] or []
        if callbacks:
            body.extend(f"- Unity callback: `{callback}`" for callback in callbacks)
        else:
            body.append("- No Unity lifecycle method detected in static scan.")
        body.extend(
            [
                "",
                "Representative classes:",
            ]
        )
        classes = module["classes"] or []
        if classes:
            body.extend(f"- `{class_name}`" for class_name in classes[:12])
        else:
            body.append("- None detected.")
        body.extend(
            [
                "",
                "Open questions:",
                "- Which scene, prefab, or ScriptableObject initializes this module?",
                "- Which config or data assets drive this module?",
                "- Is this module runtime-critical or editor-only?",
                "",
            ]
        )
    return frontmatter("Code Roadmap", "summary", ["unity", "code-roadmap", "module"]) + "\n".join(body)


def markdown_list(items: list[str], empty: str) -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- `{item}`" for item in items]


def render_scene_index(scan: dict[str, Any]) -> str:
    body = [
        "# Scene Index",
        "",
        generated_notice(),
        "## Scenes",
        "",
        *markdown_list(scan["scenes"], "No scenes found in static scan."),
        "",
        "## Prefabs",
        "",
        *markdown_list(scan["prefabs"], "No prefabs listed in static scan."),
    ]
    return frontmatter("Scene Index", "summary", ["unity", "scene"]) + "\n".join(body)


def render_config_index(scan: dict[str, Any]) -> str:
    body = [
        "# Config Index",
        "",
        generated_notice(),
        "## Assembly Definitions",
        "",
        *markdown_list(scan["asmdefs"], "No assembly definitions found."),
        "",
        "## Config and Data Files",
        "",
        *markdown_list(scan["configs"], "No config or data files listed."),
        "",
        "## Packages",
        "",
    ]
    if scan["packages"]:
        body.extend(f"- `{name}`: `{version}`" for name, version in sorted(scan["packages"].items()))
    else:
        body.append("- No packages parsed.")
    return frontmatter("Config Index", "summary", ["unity", "config", "package"]) + "\n".join(body)


GENERATED_PAGES = {
    "home.md": render_home,
    "project-map.md": render_project_map,
    "module-index.md": render_module_index,
    "code-roadmap.md": render_code_roadmap,
    "scene-index.md": render_scene_index,
    "config-index.md": render_config_index,
}


def count_indexed_pages(knowledge: Path) -> int:
    count = 0
    for subdir in ["entities", "concepts", "comparisons", "queries", "decisions"]:
        root = knowledge / subdir
        if root.is_dir():
            count += len(list(root.glob("*.md")))
    count += len([name for name in GENERATED_PAGES if (knowledge / name).is_file()])
    return count


def update_index(knowledge: Path, dry_run: bool) -> None:
    index_path = knowledge / "index.md"
    if index_path.is_file():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = "# Agent Knowledge Index\n\n## Summaries\n\n" + INDEX_BEGIN + "\n" + INDEX_END + "\n"
    generated_entries = [
        f"- {wiki_link(name)} - Generated Unity project navigation page."
        for name in GENERATED_PAGES
        if (knowledge / name).is_file() or dry_run
    ]
    block = INDEX_BEGIN + "\n" + "\n".join(generated_entries) + "\n" + INDEX_END
    if INDEX_BEGIN in text and INDEX_END in text:
        text = re.sub(
            re.escape(INDEX_BEGIN) + r".*?" + re.escape(INDEX_END),
            block,
            text,
            flags=re.DOTALL,
        )
    else:
        text = text.rstrip() + "\n\n## Summaries\n\n" + block + "\n"
    text = re.sub(r"Last updated: .*? \| Total pages: \d+", f"Last updated: {today()} | Total pages: {count_indexed_pages(knowledge)}", text)
    write_page(index_path, text, dry_run)


def refresh(project: Path, knowledge: Path, dry_run: bool = False) -> int:
    if not is_unity_project(project):
        print("Not a Unity project. No files were written.")
        for message in validation_messages(project):
            print(f"- {message}")
        return 2

    scan = scan_project(project)
    created: list[str] = []
    updated: list[str] = []

    scan_id = timestamp_slug()
    scan_json_path = knowledge / "raw" / "scans" / f"project-scan-{scan_id}.json"
    scan_path = knowledge / "raw" / "scans" / f"project-scan-{scan_id}.md"
    if not dry_run:
        scan_path.parent.mkdir(parents=True, exist_ok=True)
    write_page(scan_json_path, json.dumps(scan, indent=2, ensure_ascii=False), dry_run)
    created.append(scan_json_path.relative_to(project).as_posix())
    write_page(scan_path, render_scan_markdown(scan, scan_json_path.relative_to(project).as_posix()), dry_run)
    created.append(scan_path.relative_to(project).as_posix())

    for filename, renderer in GENERATED_PAGES.items():
        path = knowledge / filename
        existed = path.exists()
        write_page(path, renderer(scan), dry_run)
        rel_path = path.relative_to(project).as_posix()
        (updated if existed else created).append(rel_path)

    update_index(knowledge, dry_run)
    updated.append((knowledge / "index.md").relative_to(project).as_posix())
    append_log(knowledge, "refresh", "Unity static roadmaps", created, updated, dry_run)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh generated Unity agent knowledge pages.")
    parser.add_argument("--project", default=".", help="Unity project root.")
    parser.add_argument("--knowledge-dir", default="Docs/AgentKnowledge", help="Knowledge directory relative to project root.")
    parser.add_argument("--dry-run", action="store_true", help="Print intended writes without modifying files.")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    knowledge = (project / args.knowledge_dir).resolve()
    return refresh(project, knowledge, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
