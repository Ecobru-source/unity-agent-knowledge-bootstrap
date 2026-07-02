# Agent Knowledge Schema

## Domain

This wiki covers the Unity project in this repository: code structure, systems, scenes, configuration, design concepts, durable decisions, and filed analysis.

## Conventions

- File names use lowercase hyphen-case.
- Every non-raw wiki page starts with YAML frontmatter.
- Use `[[wikilinks]]` for cross-references.
- Update `updated` when changing a page.
- Add new pages to `index.md`.
- Append every scaffold, refresh, lint, or meaningful knowledge update to `log.md`.
- Keep raw files under `raw/` immutable.
- Do not copy large source files into wiki pages; summarize paths, responsibilities, entry points, dependencies, and open questions.

## Frontmatter

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

## Raw Frontmatter

```yaml
---
source: local-unity-project
generated: YYYY-MM-DDTHH:MM:SS
sha256: BODY_HASH
---
```

## Tag Taxonomy

- unity
- project-map
- code-roadmap
- module
- scene
- config
- package
- editor-tool
- gameplay
- ui
- economy
- save
- analytics
- monetization
- content
- decision
- query
- scan

## Confidence Policy

- `medium`: generated from static scan or plausible path/name evidence.
- `high`: verified by reading concrete source, scene, prefab, ScriptableObject, or config files.
- `low`: weak hypothesis or unresolved question.

## Page Thresholds

Create a page when it helps future agents avoid repeated rediscovery. Avoid pages for passing mentions, generated files, and third-party internals unless the project depends on them directly.

## Update Policy

When new evidence conflicts with an existing page:

1. Preserve both claims with dates and sources.
2. Mark `confidence` appropriately.
3. Add an open question or a decision page if user review is needed.
