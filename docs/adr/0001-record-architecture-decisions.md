# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-07

## Context

I want a record of *why* the important technical choices on this project were made, not just what they were. Useful later, and useful in interviews.

## Decision

Short Architecture Decision Records in `docs/adr/`, numbered sequentially, with a one-line summary of each in `DECISIONS.md`. Each captures context, decision, and the trade-offs accepted. Kept light so I actually write them.

## Consequences

- Decisions live in git history next to the code that implements them.
- Doubles as interview prep.
- Minor ongoing cost: one short file per non-trivial decision.
