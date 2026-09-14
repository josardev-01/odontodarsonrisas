---
name: efficient-token-workflow
description: Reduce token and tool-call cost during multi-step software engineering, research, debugging, and repository work while preserving correctness, security, verification, and user-visible quality. Use for long or iterative tasks, large repositories, multi-agent work, or whenever the user asks for economical token usage.
---

# Efficient Token Workflow

Optimize total work, not merely response length. Never save tokens by skipping required safety checks, applicable skills, evidence, tests, or explicit user requirements.

## Compact contract

Retain only the requested outcome and acceptance criteria, confirmed constraints, current repository state, changed files, open risks, and next executable action. Do not restate or reload established information unless it may have changed or exact evidence is required.

## Progressive discovery

- Search before opening files and read the smallest relevant region.
- Prefer current code, tests, schemas, and configuration over summaries.
- Batch independent read-only checks when outputs remain understandable.
- Reuse existing scripts, fixtures, templates, and lockfiles.
- Browse only for freshness, uncertainty, explicit sourcing, or high-stakes accuracy; prefer primary sources.

## Economical execution

- Build coherent vertical increments; avoid speculative edits and unrelated refactors.
- Use deterministic tools for mechanical work.
- Delegate only bounded independent work whose benefit exceeds coordination overhead. Give minimum sufficient context and do not duplicate it.
- Separate parallel ownership by files or domains and consolidate once.

## Proportional verification

Run narrow meaningful checks first and broader integration checks after stabilization. Re-run only checks affected by later changes. Never reduce verification for health, identity, payment, security, migrations, or concurrency merely to save tokens.

After a failure, retain the root cause and changed invariant instead of repeatedly reproducing verbose output.

## Compact communication

- Report outcomes, blockers, and changed assumptions rather than routine commands.
- Final responses lead with completion, verification evidence, remaining risks, and exact next user action.
- Include commands only when the user must run them, identifying the shell when relevant.

## Checkpoint and stopping

For long tasks, maintain a compact checkpoint with branch/commit, changed files, tests, decisions, blockers, and next action. After compaction, resume from it and verify only drift-prone facts.

Stop exploring when acceptance criteria have proportionate evidence. Stop retrying once an external permission, credential, quota, or service blocker is confirmed; provide one precise recovery action.
