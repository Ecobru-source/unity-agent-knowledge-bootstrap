#!/usr/bin/env python3
"""Smoke tests for unity-agent-knowledge-bootstrap scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "minimal-unity-project"


def run(args: list[str], expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != expect:
        print("COMMAND:", " ".join(args))
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        raise AssertionError(f"expected exit {expect}, got {result.returncode}")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="unity-agent-knowledge-smoke-") as tmp:
        tmp_path = Path(tmp)
        project = tmp_path / "project"
        shutil.copytree(FIXTURE, project)

        scan = run([sys.executable, str(SCRIPTS / "scan_unity_project.py"), "--project", str(project), "--json"])
        scan_data = json.loads(scan.stdout)
        assert scan_data["is_unity_project"] is True
        assert scan_data["counts"]["csharp_files"] == 1
        assert scan_data["counts"]["modules"] >= 1

        dry = run([sys.executable, str(SCRIPTS / "scaffold_unity_agent_knowledge.py"), "--project", str(project), "--dry-run"])
        assert "Would write" in dry.stdout
        assert not (project / "AGENTS.md").exists()

        run([sys.executable, str(SCRIPTS / "scaffold_unity_agent_knowledge.py"), "--project", str(project)])
        assert (project / "AGENTS.md").is_file()
        assert (project / ".rgignore").is_file()
        assert (project / "Docs" / "AgentKnowledge" / "code-roadmap.md").is_file()
        scan_dir = project / "Docs" / "AgentKnowledge" / "raw" / "scans"
        assert list(scan_dir.glob("*.json"))
        assert list(scan_dir.glob("*.md"))

        lint = run([sys.executable, str(SCRIPTS / "lint_unity_agent_knowledge.py"), "--project", str(project)])
        assert "No issues found." in lint.stdout

        non_unity = tmp_path / "not-unity"
        non_unity.mkdir()
        blocked = run(
            [sys.executable, str(SCRIPTS / "scaffold_unity_agent_knowledge.py"), "--project", str(non_unity)],
            expect=2,
        )
        assert "No files were written" in blocked.stdout
        assert not (non_unity / "AGENTS.md").exists()
        assert not (non_unity / "Docs").exists()

        refresh_blocked = run(
            [sys.executable, str(SCRIPTS / "refresh_unity_agent_knowledge.py"), "--project", str(non_unity)],
            expect=2,
        )
        assert "No files were written" in refresh_blocked.stdout
        assert not (non_unity / "Docs").exists()

    print("smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
