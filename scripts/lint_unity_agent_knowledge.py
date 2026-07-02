#!/usr/bin/env python3
"""Lint a Unity agent knowledge base."""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import defaultdict
from pathlib import Path


REQUIRED_FILES = ["SCHEMA.md", "index.md", "log.md", "home.md"]
REQUIRED_DIRS = ["raw", "raw/scans", "entities", "concepts", "comparisons", "queries", "decisions"]
PAGE_DIRS = ["entities", "concepts", "comparisons", "queries", "decisions"]


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, body


def page_slug(path: Path) -> str:
    return path.stem


def iter_wiki_pages(knowledge: Path) -> list[Path]:
    pages: list[Path] = []
    for name in ["home.md", "project-map.md", "module-index.md", "code-roadmap.md", "scene-index.md", "config-index.md"]:
        path = knowledge / name
        if path.is_file():
            pages.append(path)
    for subdir in PAGE_DIRS:
        root = knowledge / subdir
        if root.is_dir():
            pages.extend(sorted(root.glob("*.md")))
    return pages


def extract_links(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", text)


def lint(project: Path, knowledge_relative: str, strict: bool) -> int:
    knowledge = project / knowledge_relative
    errors: list[str] = []
    warnings: list[str] = []

    if not knowledge.is_dir():
        errors.append(f"Missing knowledge directory: {knowledge}")
        print_report(errors, warnings)
        return 1

    for rel_path in REQUIRED_FILES:
        if not (knowledge / rel_path).is_file():
            errors.append(f"Missing required file: {knowledge_relative}/{rel_path}")
    for rel_path in REQUIRED_DIRS:
        if not (knowledge / rel_path).is_dir():
            errors.append(f"Missing required directory: {knowledge_relative}/{rel_path}/")

    pages = iter_wiki_pages(knowledge)
    slug_to_page = {page_slug(path): path for path in pages}
    inbound: dict[str, list[str]] = defaultdict(list)
    all_links: list[tuple[Path, str]] = []
    index_text = (knowledge / "index.md").read_text(encoding="utf-8") if (knowledge / "index.md").is_file() else ""

    for path in pages:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        if not frontmatter:
            errors.append(f"Missing frontmatter: {path.relative_to(project)}")
        else:
            for key in ["title", "created", "updated", "type", "tags", "sources"]:
                if key not in frontmatter:
                    errors.append(f"Missing frontmatter key `{key}`: {path.relative_to(project)}")
        if len(text.splitlines()) > 220:
            warnings.append(f"Large page may need splitting: {path.relative_to(project)}")
        for link in extract_links(body):
            all_links.append((path, link))
            inbound[link].append(path.relative_to(project).as_posix())
        if f"[[{path.stem}]]" not in index_text and path.name not in {"home.md"}:
            warnings.append(f"Page not listed in index.md: {path.relative_to(project)}")

    for source, link in all_links:
        if link not in slug_to_page:
            warnings.append(f"Broken wikilink in {source.relative_to(project)}: [[{link}]]")

    for slug, path in slug_to_page.items():
        if path.name in {"home.md", "project-map.md"}:
            continue
        if slug not in inbound:
            warnings.append(f"Orphan page with no inbound links: {path.relative_to(project)}")

    raw_root = knowledge / "raw"
    if raw_root.is_dir():
        for raw_path in sorted(raw_root.rglob("*.md")):
            text = raw_path.read_text(encoding="utf-8")
            frontmatter, body = split_frontmatter(text)
            expected = frontmatter.get("sha256")
            if expected:
                actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
                if actual != expected:
                    warnings.append(f"Raw source hash drift: {raw_path.relative_to(project)}")

    print_report(errors, warnings)
    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


def print_report(errors: list[str], warnings: list[str]) -> None:
    print("# Unity Agent Knowledge Lint")
    print("")
    if not errors and not warnings:
        print("No issues found.")
        return
    if errors:
        print("## Errors")
        print("")
        for item in errors:
            print(f"- {item}")
        print("")
    if warnings:
        print("## Warnings")
        print("")
        for item in warnings:
            print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a Unity agent knowledge base.")
    parser.add_argument("--project", default=".", help="Unity project root.")
    parser.add_argument("--knowledge-dir", default="Docs/AgentKnowledge", help="Knowledge directory relative to project root.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings exist.")
    args = parser.parse_args()
    return lint(Path(args.project).resolve(), args.knowledge_dir, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
