---
tags:
  - research
  - field-notes
  - methods
---

# Experiment Log

This is a fictional working note from the Atlas spring pilot. It demonstrates the kind of mixed Markdown that should remain readable when published: a short status update, a code fragment, a calculation, and links back to the method.

## 2026-04-18 | Pilot review

> [!warning] Synthetic data
> Names, measurements, and locations on this page are invented for documentation examples. They are not operational records.

The review compared three observation routes against the [[Research/Signal Quality|signal quality rubric]]. The route score is a simple weighted average:

$$Q = 0.4T + 0.3F + 0.2C + 0.1R$$

where $T$ is traceability, $F$ freshness, $C$ context, and $R$ reuse. With a normalized pilot result of $T=1.0$, $F=0.92$, $C=0.83$, and $R=1.0$, the score is $Q=0.943$.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    route: str
    traceability: float
    freshness: float


observations = [
    Observation("north", 1.00, 0.95),
    Observation("central", 1.00, 0.90),
    Observation("south", 1.00, 0.91),
]
average_freshness = sum(item.freshness for item in observations) / len(observations)
print(f"average freshness: {average_freshness:.2f}")
```

## Decision log

- Keep source links close to claims so a reader can inspect context.
- Use a callout for caveats instead of burying them in a footer.
- Keep the raw note unchanged when opening it in [[Slides/VaultPub in 90 Seconds|Slide View]].

The next review will compare this log with the [[Guides/Obsidian Patterns|rendering gallery]]. #field-notes
