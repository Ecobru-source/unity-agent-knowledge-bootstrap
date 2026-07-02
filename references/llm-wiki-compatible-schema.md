# LLM Wiki Compatible Schema

This skill embeds the minimum Karpathy-style LLM Wiki workflow needed for a Unity project. The target wiki is project-local and lives at `Docs/AgentKnowledge/`.

## Directory Layout

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

## Layers

- `raw/`: immutable source material and generated scans. Agents may read these files but should not edit old raw files.
- `entities/`: notable project entities such as systems, modules, tools, scenes, data assets, and third-party packages.
- `concepts/`: design or technical concepts such as economy loop, order flow, save lifecycle, or content pipeline.
- `comparisons/`: side-by-side analysis worth preserving.
- `queries/`: filed answers that would be expensive to re-derive.
- `decisions/`: durable decisions, tradeoffs, and rationale.

## Required Root Files

- `SCHEMA.md`: conventions, tag taxonomy, page thresholds, and update policy.
- `index.md`: catalog of pages with one-line summaries.
- `log.md`: append-only chronological record of wiki actions.
- `home.md`: entry point for future agents.

## Page Frontmatter

Every non-raw wiki page should start with:

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | decision | summary
tags: [unity]
sources: []
confidence: medium
---
```

Use `confidence: high` only after verification from concrete project files. Use `confidence: low` for guesses, weakly supported hypotheses, or pages that need review.

## Raw Frontmatter

Raw generated scans should use:

```yaml
---
source: local-unity-project
generated: YYYY-MM-DDTHH:MM:SS
sha256: BODY_HASH
---
```

The `sha256` is computed over the body below the frontmatter. If the hash changes later, the raw file has drifted and should be reported by lint.

## Link Rules

- Use `[[wikilinks]]` for project knowledge pages.
- New or updated pages should link to at least two related pages when possible.
- Do not force links when the wiki is brand new; record open questions instead.

## Index Rules

- Every entity, concept, comparison, query, decision, and summary page should appear in `index.md`.
- Keep entries short: wikilink plus one-line summary.
- Scripts may update a marked generated block in `index.md`.

## Log Rules

Append one log entry per scaffold, refresh, lint, or meaningful manual update:

```markdown
## [YYYY-MM-DD] action | subject
- Created: path
- Updated: path
```

Do not rewrite old log entries.

## Page Thresholds

Create a page when:

- the entity or concept is central to the Unity project, or
- it is referenced by multiple source files, configs, scenes, or discussions, or
- it would save future agents from repeated rediscovery.

Do not create pages for passing mentions, third-party implementation details, or noisy generated files.

## Lint Expectations

Lint should report:

- missing required root files
- missing required directories
- broken wikilinks
- wiki pages missing from `index.md`
- pages without frontmatter
- tags not listed in `SCHEMA.md`
- raw source hash drift
- pages over roughly 200 lines
- orphan pages with no inbound links
