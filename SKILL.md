---
name: unity-agent-knowledge-bootstrap
description: Bootstrap an existing Unity project as an efficient Codex or Claude agent root by creating project-local agent rules, .rgignore noise filters, a Karpathy-style LLM Wiki knowledge base under Docs/AgentKnowledge, static Unity scans, and medium-confidence code roadmaps. Use when the user asks to prepare, onboard, index, refresh, lint, or reduce token usage for a Unity project used as an agent workspace. This skill does not modify gameplay code, prefabs, scenes, ProjectSettings, Packages, or business logic.
---

# Unity Agent Knowledge Bootstrap

## Overview

Prepare a Unity project so future agents can orient themselves through a small, project-local knowledge base instead of repeatedly scanning the full repository. The skill installs agent guidance, search ignore rules, LLM Wiki compatible files, static project scans, and generated roadmaps without touching Unity business files.

## Safety Boundary

Default to non-business changes only. This skill may create or update:

- `AGENTS.md`
- `.rgignore`
- `Docs/AgentKnowledge/**`

## Write Authorization

Treat every non-dry-run scaffold or refresh as a local write operation that needs explicit user confirmation.

Always:

- run `--dry-run` before scaffold or refresh when preparing a real user project
- summarize the exact files or managed blocks that will be created or updated
- ask for confirmation before running the same command without `--dry-run`
- stop without writing when the target is not a Unity project

Do not modify:

- `Assets/Scripts/**`
- `Assets/Prefabs/**`
- `Assets/Scenes/**`
- `ProjectSettings/**`
- `Packages/**`
- gameplay, economy, UI, save, monetization, analytics, or content configuration

Generated roadmaps are navigation aids, not verified truth. Mark auto-generated code roadmaps as `confidence: medium` until an agent verifies the relevant source, scene, prefab, or config files for a specific task.

## Workflow

### 1. Audit the Target

Confirm the target is a Unity project before writing anything. A valid target normally has:

- `Assets/`
- `Packages/manifest.json`
- `ProjectSettings/`

Run:

```bash
python3 scripts/scan_unity_project.py --project /path/to/UnityProject --json
```

Use the JSON or Markdown scan to explain what will be initialized, especially when `AGENTS.md`, `.rgignore`, or `Docs/AgentKnowledge` already exist.
Do not proceed to write operations until the user confirms the target and planned changes.

### 2. Scaffold the Agent Knowledge Layer

Run:

```bash
python3 scripts/scaffold_unity_agent_knowledge.py --project /path/to/UnityProject --dry-run
python3 scripts/scaffold_unity_agent_knowledge.py --project /path/to/UnityProject
```

After the dry-run, stop and summarize the planned writes. Continue with the non-dry-run command only after explicit user confirmation.

The scaffold script:

- creates `Docs/AgentKnowledge/`
- creates LLM Wiki compatible `SCHEMA.md`, `index.md`, `log.md`, and `home.md`
- adds an agent guidance block to `AGENTS.md`
- adds a Unity noise-filter block to `.rgignore`
- creates wiki subdirectories for `raw`, `entities`, `concepts`, `comparisons`, `queries`, and `decisions`
- runs a refresh pass unless `--no-refresh` is provided
- exits before writing anything when the target is not a Unity project

Existing `AGENTS.md` and `.rgignore` files are updated through marked blocks, not overwritten.

### 3. Refresh the Roadmaps

Run this when the Unity project structure changes:

```bash
python3 scripts/refresh_unity_agent_knowledge.py --project /path/to/UnityProject
```

For a real user project, first run the same command with `--dry-run`, summarize the generated pages and raw scan files, and ask for confirmation before writing.

Refresh writes:

- `raw/scans/project-scan-YYYY-MM-DD-HHMMSS.md`
- `raw/scans/project-scan-YYYY-MM-DD-HHMMSS.json`
- `project-map.md`
- `module-index.md`
- `code-roadmap.md`
- `scene-index.md`
- `config-index.md`

The JSON scan preserves the complete structured scan. The Markdown scan is capped for readability and links to the JSON. Do not copy full source code into the wiki. Store paths, roles, entry points, dependency hints, open questions, and confidence levels.

### 4. Lint the Knowledge Base

Run:

```bash
python3 scripts/lint_unity_agent_knowledge.py --project /path/to/UnityProject
```

The lint pass checks required files, broken `[[wikilinks]]`, missing index entries, frontmatter, raw source hash drift, orphan pages, and oversized pages.

### 5. Validate the Skill Package

Before packaging or publishing this skill, run:

```bash
python3 tests/smoke_test.py
```

The smoke test covers scan, dry-run scaffold, real scaffold, lint, and non-Unity directory blocking against the bundled minimal Unity fixture.

## LLM Wiki Integration

This skill embeds the minimal Karpathy-style LLM Wiki workflow needed for Unity project onboarding. Do not assume the user's machine has a separate `llm-wiki` skill installed.

The target wiki lives inside the Unity project:

```text
Docs/AgentKnowledge/
├── SCHEMA.md
├── index.md
├── log.md
├── home.md
├── raw/
│   ├── scans/
│   ├── notes/
│   └── assets/
├── entities/
├── concepts/
├── comparisons/
├── queries/
└── decisions/
```

Use `references/llm-wiki-compatible-schema.md` for detailed wiki rules.

## Unity Scan Rules

Default scan paths should favor high-signal project structure:

- `Assets/Scripts/`
- `Assets/Editor/`
- `Assets/Resources/`
- `Assets/StreamingAssets/`
- `Assets/**/Configs*/`
- `Packages/manifest.json`
- `Packages/packages-lock.json`
- `ProjectSettings/`
- `*.asmdef`
- `*.asmref`
- small text configuration files

Default ignored paths:

- `Library/`
- `Temp/`
- `Logs/`
- `Builds/`
- `Obj/`
- `UserSettings/`
- `MemoryCaptures/`
- generated IDE files
- large binary assets

Use `references/unity-project-scan-rules.md` for the full scan policy.

## Agent Root Integration

When the Unity project is already the agent root, scaffold in place and then recommend a fresh orientation:

- Continue current work: ask the user to run `/compact` with a short focus on the initialized knowledge base.
- Start serious project work: ask the user to run `/clear`, then let the new session read `AGENTS.md`, `Docs/AgentKnowledge/home.md`, and `Docs/AgentKnowledge/project-map.md`.

Use `references/agent-root-integration.md` for details.

## Resources

### scripts/

- `scan_unity_project.py`: read-only static Unity project scan.
- `scaffold_unity_agent_knowledge.py`: create or update the agent knowledge layer.
- `refresh_unity_agent_knowledge.py`: regenerate scan-derived roadmaps.
- `lint_unity_agent_knowledge.py`: check wiki structure and integrity.

### references/

- `unity-project-scan-rules.md`: what to scan, summarize, and ignore.
- `llm-wiki-compatible-schema.md`: wiki structure, frontmatter, links, log, and lint rules.
- `agent-root-integration.md`: how to update an existing agent root safely.

### assets/templates/

Templates copied or inserted into the target project during scaffold.

### tests/

- `tests/smoke_test.py`: end-to-end regression test for the bundled scripts.
- `tests/fixtures/minimal-unity-project/`: minimal Unity fixture used by the smoke test.
