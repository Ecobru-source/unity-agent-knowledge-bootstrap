## Unity Agent Knowledge

This Unity project keeps a project-local agent knowledge base at `Docs/AgentKnowledge/`.

Before project analysis or implementation, orient through:

1. `Docs/AgentKnowledge/home.md`
2. `Docs/AgentKnowledge/project-map.md`
3. `Docs/AgentKnowledge/code-roadmap.md`
4. any task-relevant pages from `Docs/AgentKnowledge/index.md`

Default search behavior:

- Prefer `rg` and targeted file reads.
- Do not scan `Library/`, `Temp/`, `Logs/`, `Builds/`, `Obj/`, `UserSettings/`, or `MemoryCaptures/` unless a task specifically requires them.
- Treat generated roadmap pages as navigation aids with `confidence: medium` until verified against concrete source, scene, prefab, ScriptableObject, or config files.
- Do not modify Unity business files unless the user explicitly asks for a specific implementation change.

Knowledge maintenance:

- Add durable findings to `Docs/AgentKnowledge/`.
- Update `index.md` and append `log.md` when creating or updating knowledge pages.
- Keep raw scans in `Docs/AgentKnowledge/raw/scans/` immutable.
