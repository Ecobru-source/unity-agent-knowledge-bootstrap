#!/usr/bin/env python3
"""Read-only Unity project scanner for agent knowledge bootstrapping."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".vs",
    ".idea",
    "Library",
    "Temp",
    "Logs",
    "Build",
    "Builds",
    "Obj",
    "UserSettings",
    "MemoryCaptures",
    "node_modules",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".psd",
    ".tga",
    ".tif",
    ".tiff",
    ".webp",
    ".exr",
    ".wav",
    ".mp3",
    ".ogg",
    ".aiff",
    ".flac",
    ".mp4",
    ".mov",
    ".webm",
    ".avi",
    ".fbx",
    ".blend",
    ".obj",
    ".dae",
    ".max",
    ".ma",
    ".mb",
    ".apk",
    ".aab",
    ".ipa",
    ".app",
    ".exe",
    ".zip",
    ".7z",
    ".rar",
    ".dmg",
    ".ttf",
    ".otf",
    ".dll",
    ".so",
    ".bundle",
}

CONFIG_EXTENSIONS = {
    ".json",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".xml",
    ".txt",
    ".asset",
    ".asmdef",
    ".asmref",
}

UNITY_CALLBACKS = [
    "Awake",
    "Start",
    "Update",
    "FixedUpdate",
    "LateUpdate",
    "OnEnable",
    "OnDisable",
    "OnDestroy",
    "OnValidate",
]

MAX_TEXT_BYTES = 512 * 1024
MAX_LIST_ITEMS = 120
MAX_MARKDOWN_MODULES = 80
MAX_MARKDOWN_SAMPLE_FILES_PER_MODULE = 8


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def today() -> str:
    return dt.date.today().isoformat()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_unity_project(root: Path) -> bool:
    return (
        (root / "Assets").is_dir()
        and (root / "ProjectSettings").is_dir()
        and (root / "Packages" / "manifest.json").is_file()
    )


def validation_messages(root: Path) -> list[str]:
    messages: list[str] = []
    if not (root / "Assets").is_dir():
        messages.append("missing Assets/")
    if not (root / "ProjectSettings").is_dir():
        messages.append("missing ProjectSettings/")
    if not (root / "Packages" / "manifest.json").is_file():
        messages.append("missing Packages/manifest.json")
    return messages


def iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, filenames in os.walk(root):
        current_path = Path(current)
        dirs[:] = [
            d
            for d in dirs
            if d not in IGNORED_DIR_NAMES and not d.startswith(".")
        ]
        for filename in filenames:
            path = current_path / filename
            if should_ignore_file(path):
                continue
            files.append(path)
    return files


def should_ignore_file(path: Path) -> bool:
    if path.name == ".DS_Store":
        return True
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    if path.suffix.lower() in {".csproj", ".sln", ".user", ".pidb", ".booproj", ".svd"}:
        return True
    return False


def read_text_sample(path: Path) -> str:
    data = path.read_bytes()[:MAX_TEXT_BYTES]
    return data.decode("utf-8", errors="ignore")


def infer_module(relative_path: str) -> str:
    lower = relative_path.lower()
    parts = relative_path.split("/")
    if "editor" in lower:
        return "editor-tools"
    if "/ui/" in lower or "ui" in Path(relative_path).stem.lower():
        return "ui"
    if "save" in lower or "storage" in lower:
        return "save"
    if "order" in lower or "quest" in lower or "task" in lower:
        return "orders-and-tasks"
    if "merge" in lower or "board" in lower:
        return "merge-gameplay"
    if "economy" in lower or "currency" in lower or "reward" in lower:
        return "economy"
    if "iap" in lower or "purchase" in lower or "ads" in lower or "admob" in lower:
        return "monetization"
    if "analytic" in lower or "telemetry" in lower or "tracking" in lower:
        return "analytics"
    if "tutorial" in lower or "guide" in lower or "onboarding" in lower:
        return "tutorial"
    if "config" in lower or "data" in lower or "scriptable" in lower:
        return "config-data"
    if len(parts) >= 3 and parts[0] == "Assets" and parts[1] == "Scripts":
        return slug(parts[2])
    if len(parts) >= 4 and parts[0] == "Assets" and parts[2] == "Scripts":
        return slug(parts[1])
    return "uncategorized"


def slug(value: str) -> str:
    value = re.sub(r"(?<!^)(?=[A-Z])", "-", value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "uncategorized"


def parse_csharp(path: Path, root: Path) -> dict[str, Any]:
    text = read_text_sample(path)
    relative_path = rel(path, root)
    namespaces = sorted(set(re.findall(r"\bnamespace\s+([A-Za-z_][A-Za-z0-9_.]*)", text)))
    type_pattern = re.compile(
        r"(?:^|\n)\s*(?:\[[^\]]+\]\s*)*(?:public|internal|private|protected|sealed|abstract|static|partial|\s)*"
        r"\b(class|interface|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^{\n]+))?",
        re.MULTILINE,
    )
    types: list[dict[str, Any]] = []
    for kind, name, bases in type_pattern.findall(text):
        bases_list = [b.strip() for b in re.split(r",", bases or "") if b.strip()]
        types.append({"kind": kind, "name": name, "bases": bases_list[:6]})

    public_methods = sorted(
        set(
            re.findall(
                r"\b(?:public|protected|internal)\s+(?:static\s+)?(?:async\s+)?[A-Za-z0-9_<>,\[\]\.?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                text,
            )
        )
    )
    callbacks = [name for name in UNITY_CALLBACKS if re.search(rf"\b(?:void\s+)?{name}\s*\(", text)]
    serialized_fields = len(re.findall(r"\[SerializeField\]", text))
    attributes = sorted(set(re.findall(r"\[([A-Za-z_][A-Za-z0-9_]+)(?:\(|\])", text)))[:12]

    category = "plain-csharp"
    all_bases = " ".join(base for t in types for base in t.get("bases", []))
    if "MonoBehaviour" in all_bases:
        category = "mono-behaviour"
    elif "ScriptableObject" in all_bases:
        category = "scriptable-object"
    elif "Editor" in all_bases or "/Editor/" in relative_path:
        category = "editor"

    return {
        "path": relative_path,
        "module": infer_module(relative_path),
        "category": category,
        "namespaces": namespaces,
        "types": types[:12],
        "unity_callbacks": callbacks,
        "public_methods": public_methods[:20],
        "serialized_field_count": serialized_fields,
        "attributes": attributes,
    }


def load_packages(root: Path) -> dict[str, str]:
    manifest = root / "Packages" / "manifest.json"
    if not manifest.is_file():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return {}
    dependencies = data.get("dependencies", {})
    if not isinstance(dependencies, dict):
        return {}
    return {str(k): str(v) for k, v in dependencies.items()}


def scan_project(project: Path) -> dict[str, Any]:
    root = project.resolve()
    files = iter_project_files(root)
    csharp_files = [p for p in files if p.suffix.lower() == ".cs" and "Assets/" in rel(p, root)]
    scenes = sorted(rel(p, root) for p in files if p.suffix.lower() == ".unity")
    prefabs = sorted(rel(p, root) for p in files if p.suffix.lower() == ".prefab")
    asmdefs = sorted(rel(p, root) for p in files if p.suffix.lower() in {".asmdef", ".asmref"})
    configs = sorted(
        rel(p, root)
        for p in files
        if p.suffix.lower() in CONFIG_EXTENSIONS
        and (
            "ProjectSettings/" in rel(p, root)
            or "Resources/" in rel(p, root)
            or "StreamingAssets/" in rel(p, root)
            or "Config" in rel(p, root)
            or "Data" in rel(p, root)
            or p.suffix.lower() in {".asmdef", ".asmref"}
        )
    )
    csharp_summaries = [parse_csharp(p, root) for p in sorted(csharp_files)]

    modules: dict[str, dict[str, Any]] = {}
    for item in csharp_summaries:
        module = item["module"]
        entry = modules.setdefault(
            module,
            {
                "name": module,
                "file_count": 0,
                "classes": [],
                "callbacks": [],
                "categories": {},
                "sample_files": [],
            },
        )
        entry["file_count"] += 1
        entry["sample_files"].append(item["path"])
        entry["callbacks"].extend(item["unity_callbacks"])
        entry["categories"][item["category"]] = entry["categories"].get(item["category"], 0) + 1
        for type_info in item["types"]:
            if type_info["kind"] == "class":
                entry["classes"].append(type_info["name"])

    for entry in modules.values():
        entry["sample_files"] = entry["sample_files"][:12]
        entry["classes"] = sorted(set(entry["classes"]))[:24]
        entry["callbacks"] = sorted(set(entry["callbacks"]))

    packages = load_packages(root)
    return {
        "project_root": str(root),
        "generated_at": utc_now().isoformat(),
        "is_unity_project": is_unity_project(root),
        "validation_messages": validation_messages(root),
        "counts": {
            "files_scanned": len(files),
            "csharp_files": len(csharp_files),
            "scenes": len(scenes),
            "prefabs": len(prefabs),
            "asmdefs": len(asmdefs),
            "configs": len(configs),
            "packages": len(packages),
            "modules": len(modules),
        },
        "packages": packages,
        "scenes": scenes,
        "prefabs": prefabs[:MAX_LIST_ITEMS],
        "asmdefs": asmdefs,
        "configs": configs[:MAX_LIST_ITEMS],
        "modules": dict(sorted(modules.items())),
        "csharp": csharp_summaries,
    }


def markdown_list(items: list[str], limit: int = MAX_LIST_ITEMS) -> str:
    if not items:
        return "- None found\n"
    lines = [f"- `{item}`" for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"- ... {len(items) - limit} more omitted")
    return "\n".join(lines) + "\n"


def render_scan_body(scan: dict[str, Any], full_scan_json_path: str | None = None) -> str:
    counts = scan["counts"]
    lines = [
        "# Unity Project Static Scan",
        "",
        f"- Generated: {scan['generated_at']}",
        f"- Project root: `{scan['project_root']}`",
        f"- Unity project detected: `{scan['is_unity_project']}`",
    ]
    if full_scan_json_path:
        lines.append(f"- Full structured scan: `{full_scan_json_path}`")
        lines.append("- This Markdown summary is capped for readability; query the JSON for complete static scan details.")
    lines.extend(["", "## Validation", ""])
    if scan["validation_messages"]:
        lines.extend(f"- {msg}" for msg in scan["validation_messages"])
    else:
        lines.append("- Unity project markers found.")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Files scanned: {counts['files_scanned']}",
            f"- C# files: {counts['csharp_files']}",
            f"- Modules inferred: {counts['modules']}",
            f"- Scenes: {counts['scenes']}",
            f"- Prefabs listed: {counts['prefabs']}",
            f"- Assembly definitions: {counts['asmdefs']}",
            f"- Config/data files listed: {counts['configs']}",
            f"- Packages: {counts['packages']}",
            "",
            "## Modules",
            "",
        ]
    )
    module_items = list(scan["modules"].items())
    for name, module in module_items[:MAX_MARKDOWN_MODULES]:
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Files: {module['file_count']}",
                f"- Categories: `{json.dumps(module['categories'], sort_keys=True)}`",
                f"- Unity callbacks: {', '.join(module['callbacks']) if module['callbacks'] else 'None detected'}",
                f"- Classes: {', '.join(module['classes']) if module['classes'] else 'None detected'}",
                "- Sample files:",
            ]
        )
        lines.extend(f"  - `{path}`" for path in module["sample_files"][:MAX_MARKDOWN_SAMPLE_FILES_PER_MODULE])
        if len(module["sample_files"]) > MAX_MARKDOWN_SAMPLE_FILES_PER_MODULE:
            omitted = len(module["sample_files"]) - MAX_MARKDOWN_SAMPLE_FILES_PER_MODULE
            lines.append(f"  - ... {omitted} more in full JSON")
        lines.append("")
    if len(module_items) > MAX_MARKDOWN_MODULES:
        omitted = len(module_items) - MAX_MARKDOWN_MODULES
        lines.extend(
            [
                f"> Module summary truncated: {omitted} modules omitted from Markdown.",
                "> Use the full structured JSON scan for complete module details.",
                "",
            ]
        )

    lines.extend(["## Scenes", "", markdown_list(scan["scenes"])])
    lines.extend(["## Assembly Definitions", "", markdown_list(scan["asmdefs"])])
    lines.extend(["## Config and Data Files", "", markdown_list(scan["configs"])])
    lines.extend(["## Packages", ""])
    if scan["packages"]:
        for name, version in sorted(scan["packages"].items()):
            lines.append(f"- `{name}`: `{version}`")
    else:
        lines.append("- None parsed")
    lines.append("")
    return "\n".join(lines)


def add_raw_frontmatter(body: str, generated_at: str) -> str:
    persisted_body = "\n" + body.rstrip() + "\n"
    digest = hashlib.sha256(persisted_body.encode("utf-8")).hexdigest()
    return (
        "---\n"
        "source: local-unity-project\n"
        f"generated: {generated_at}\n"
        f"sha256: {digest}\n"
        "---\n"
        f"{persisted_body}"
    )


def render_scan_markdown(scan: dict[str, Any], full_scan_json_path: str | None = None) -> str:
    body = render_scan_body(scan, full_scan_json_path)
    return add_raw_frontmatter(body, scan["generated_at"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Unity project scanner.")
    parser.add_argument("--project", default=".", help="Unity project root.")
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    scan = scan_project(project)

    if args.json:
        rendered = json.dumps(scan, indent=2, ensure_ascii=False)
    else:
        rendered = render_scan_markdown(scan)

    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        print(rendered)
    return 0 if scan["is_unity_project"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
