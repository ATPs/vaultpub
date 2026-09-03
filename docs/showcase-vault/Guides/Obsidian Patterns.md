---
tags:
  - guide
  - obsidian
  - syntax
  - showcase
aliases:
  - Syntax gallery
---

# Obsidian Patterns

VaultPub keeps the source format familiar. This page collects a few patterns that appear in everyday Obsidian vaults and remain useful after publication.

## Links and embeds

Use an alias when the destination has a more precise title than the sentence needs: [[Research/Signal Quality|the signal quality study]]. Use a local embed when the attachment is part of the explanation:

![[assets/publishing-workflow.svg|760]]

The same workflow is also linked from [[README]]. A note can be discovered from either direction, and the backlinks panel makes that relationship visible.

## Diagram

```mermaid
sequenceDiagram
    participant Note as Markdown note
    participant Index as Vault index
    participant Site as Published site
    Note->>Index: scan links and tags
    Index->>Site: render article and navigation
    Site-->>Note: reload after local edit
```

## Math and code

For a compact planning estimate, the expected reading time can be modeled as:

$$t = \frac{w}{r} + b$$

where $w$ is the word count, $r$ is the reading rate, and $b$ is the time spent following links.

```yaml
note:
  source: local-markdown
  links: resolved-at-index-time
  output: article-or-slide-view
```

> [!tip] Keep the source expressive
> Headings, tables, callouts, diagrams, and equations can coexist in one note. The best showcase is a believable note, not a checklist of isolated syntax fragments.

## Related notes

The [[Research/Signal Quality|method note]] uses this style in practice. The [[Research/Experiment Log|working log]] adds a Python example and a numeric calculation. #obsidian #syntax
