# Agent Root Integration

Use this reference when the Unity project is already the active agent root.

## Integration Strategy

Scaffold in place. Do not move the Unity project and do not require a lightweight wrapper directory.

Run dry-run first, summarize the managed writes, and continue only after explicit user confirmation.

The skill should add only:

- a marked block in `AGENTS.md`
- a marked block in `.rgignore`
- `Docs/AgentKnowledge/`

## AGENTS.md Update

If `AGENTS.md` exists, preserve all existing content and update only:

```markdown
<!-- BEGIN UNITY AGENT KNOWLEDGE -->
...
<!-- END UNITY AGENT KNOWLEDGE -->
```

If `AGENTS.md` does not exist, create a minimal one containing the same block.

## .rgignore Update

If `.rgignore` exists, preserve all existing content and update only:

```text
# BEGIN UNITY AGENT KNOWLEDGE IGNORE
...
# END UNITY AGENT KNOWLEDGE IGNORE
```

If `.rgignore` does not exist, create it.

## After Bootstrap

The current session may already contain noisy exploration history. After scaffold:

- for the same task, suggest `/compact` with a short focus on the initialized knowledge layer
- for a new project work session, suggest `/clear`

Future agents should orient through:

1. `AGENTS.md`
2. `Docs/AgentKnowledge/home.md`
3. `Docs/AgentKnowledge/project-map.md`
4. task-relevant roadmap or wiki pages

## Existing Knowledge Base

If `Docs/AgentKnowledge/` already exists:

- read `SCHEMA.md`
- read `index.md`
- scan the last entries of `log.md`
- do not overwrite human-authored pages
- update managed generated pages and append log entries
