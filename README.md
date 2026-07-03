# Unity Agent Knowledge Bootstrap

Bootstrap a full Unity project into an efficient AI-agent workspace without touching gameplay code.

This skill helps Codex, Claude, or another coding agent orient inside a real Unity project by creating a small project-local knowledge layer:

- agent rules in `AGENTS.md`
- Unity noise filters in `.rgignore`
- a Karpathy-style LLM Wiki under `Docs/AgentKnowledge/`
- static project scans
- medium-confidence roadmaps for scripts, scenes, configs, and modules

It is designed for complete, non-lightweight Unity projects where `Library/`, `Temp/`, generated files, binary assets, and repeated repository scans waste context tokens.

## Why This Exists

Full Unity projects are usually noisy agent roots.

An agent can technically open the whole project, but it will often spend context on:

- Unity caches and temporary files
- IDE-generated metadata
- build outputs
- large binary assets
- repeated directory exploration
- stale assumptions about scripts, scenes, and configs

This skill adds a small, refreshable navigation layer so future agents can start from stable project knowledge instead of repeatedly rediscovering the repository.

## What It Creates

In the target Unity project, the scaffold may create or update only:

```text
AGENTS.md
.rgignore
Docs/AgentKnowledge/
```

The generated knowledge base includes:

```text
Docs/AgentKnowledge/
+-- SCHEMA.md
+-- home.md
+-- index.md
+-- log.md
+-- project-map.md
+-- module-index.md
+-- code-roadmap.md
+-- scene-index.md
+-- config-index.md
+-- raw/
|   +-- scans/
+-- entities/
+-- concepts/
+-- comparisons/
+-- queries/
+-- decisions/
```

The raw JSON scan preserves complete structured scan data. The Markdown scan is capped for readability and links back to the JSON file.

## Safety Boundary

This skill is intentionally non-business by default.

It does not modify:

- `Assets/Scripts/**`
- `Assets/Prefabs/**`
- `Assets/Scenes/**`
- `ProjectSettings/**`
- `Packages/**`
- gameplay logic
- economy data
- UI behavior
- save systems
- monetization
- analytics
- content configuration

Generated roadmaps are navigation aids, not verified truth. Treat them as `confidence: medium` until an agent checks the relevant source, scene, prefab, or config files for a specific task.

## Quick Start

Download the release asset:

[unity-agent-knowledge-bootstrap.zip](https://github.com/Ecobru-source/unity-agent-knowledge-bootstrap/releases/tag/v0.1.0)

Use the release asset, not GitHub's auto-generated "Source code (zip)", when installing the packaged skill.

Then ask Codex to use the skill on a Unity project, for example:

```text
Use $unity-agent-knowledge-bootstrap to initialize an agent knowledge base for this Unity project.
```

If you run the bundled scripts manually from this repository, use:

```bash
python3 scripts/scan_unity_project.py --project /path/to/UnityProject --json
python3 scripts/scaffold_unity_agent_knowledge.py --project /path/to/UnityProject --dry-run
python3 scripts/scaffold_unity_agent_knowledge.py --project /path/to/UnityProject
python3 scripts/lint_unity_agent_knowledge.py --project /path/to/UnityProject
```

Run a refresh after meaningful project structure changes:

```bash
python3 scripts/refresh_unity_agent_knowledge.py --project /path/to/UnityProject
```

## Typical Workflow

1. Confirm the target is a Unity project.
2. Scan the project and explain what will be initialized.
3. Run scaffold in dry-run mode.
4. Scaffold the knowledge layer.
5. Refresh scan-derived roadmaps.
6. Lint the knowledge base.
7. For an existing agent root, start future work from `AGENTS.md`, `Docs/AgentKnowledge/home.md`, and `Docs/AgentKnowledge/project-map.md`.

## What Gets Ignored

The generated `.rgignore` block is tuned for Unity agent work and defaults to ignoring:

- `Library/`
- `Temp/`
- `Logs/`
- `Builds/`
- `Obj/`
- `UserSettings/`
- `MemoryCaptures/`
- generated IDE files
- large binary assets

This reduces search noise and helps agents spend context on scripts, configs, scenes, packages, and project settings that are more likely to matter.

## Included Scripts

- `scripts/scan_unity_project.py`: read-only static Unity project scan.
- `scripts/scaffold_unity_agent_knowledge.py`: create or update the agent knowledge layer.
- `scripts/refresh_unity_agent_knowledge.py`: regenerate scan-derived roadmaps.
- `scripts/lint_unity_agent_knowledge.py`: check wiki structure and integrity.

## Validation

The repository includes a minimal Unity fixture and smoke test:

```bash
python3 tests/smoke_test.py
```

The smoke test covers scan, dry-run scaffold, real scaffold, lint, and non-Unity directory blocking.

## When To Use It

Use this when:

- a complete Unity project is used directly as an agent root
- token usage is dominated by Unity project noise
- future agents need a stable project orientation layer
- you want project-local knowledge rather than an external personal knowledge base
- you want static roadmaps before deeper task-specific code reading

Do not use it as an automatic business refactor tool. It prepares the workspace; it does not change game behavior.

## Release

Current release:

[v0.1.0](https://github.com/Ecobru-source/unity-agent-knowledge-bootstrap/releases/tag/v0.1.0)
