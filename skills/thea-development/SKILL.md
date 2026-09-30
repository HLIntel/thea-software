---
name: thea-development
description: Develop, debug, refactor, review, or plan software with Thea-style context routing and proof-of-change. Use for coding work where context efficiency, repository navigation, verification, anti-drift, or agent handoff matters.
user-invocable: true
---

# thea-development — route → load → change → prove → compact

A development skill derived from Thea Software's engineering contract. It complements the `thea`
failure-ledger skill: this skill performs development work; `thea` records a failure shape when the
work exposes one.

The objective is not to read more. It is to obtain the smallest sufficient context that can produce
and prove the requested change.

## Operating invariant

**No claim of completion without a named proof. No context without a reason to load it.**

Use repository state as memory. Prefer stable ids, paths, symbols, diffs, gate names and command
results over prose summaries that can drift.

## Loop

### 1. ROUTE — identify the smallest work surface

Start from the user's objective, not the repository tree.

If Thea is installed:

```bash
thea port <target> --frame agent
thea plan <target> --task <task> --change <class> --json
```

Use `narrow` for a file/symbol-sized task, `code` for a component, and `codebase` only when the
task genuinely crosses architectural layers.

If the target is unknown:
1. search names, symbols, errors, routes, tests or imports;
2. identify likely entry points;
3. inspect only enough neighboring structure to establish ownership;
4. route again once a concrete target exists.

Do not inventory the repository first.

### 2. LOAD — build a bounded context set

Load context in this order:

1. task contract: objective, constraints, stop condition;
2. target file or exact relevant range;
3. directly imported/called definitions needed to understand the change;
4. tests that specify the affected behavior;
5. local instructions/configuration named by the route;
6. only then broader architecture or documentation if an unresolved question requires it.

Prefer symbol/range reads over whole files, search results over directory dumps, diffs over rereading
unchanged files, authoritative declarations over generated prose, primary repository state over
remembered commands, and one relevant language/tool manifest over global tool catalogs.

Every newly loaded item should answer a live question. If it does not, stop loading.

### 3. CONTRACT — keep one compact working record

Maintain this logical record during the task:

```text
GOAL       exact requested outcome
TARGETS    paths/symbols allowed to change
FACTS      confirmed repository facts
ASSUMED    unresolved assumptions that affect implementation
GATES      proofs required before done
CHANGED    paths actually modified
BLOCKERS   facts or permissions preventing completion
NEXT       single next action
```

Keep values terse. Do not duplicate file contents in the record. If a fact is cheaply recoverable,
store its pointer rather than a prose explanation.

### 4. CHANGE — make the smallest coherent edit

Before adding code, search for an existing implementation, abstraction, convention or utility that
already owns the behavior.

Rules:
- modify the narrowest responsible layer;
- preserve public behavior unless the task explicitly changes it;
- avoid speculative abstractions;
- do not add infrastructure merely to support the current edit;
- do not raise limits to make an implementation fit;
- do not silently repair unrelated code;
- keep generated files generated;
- prefer deterministic, machine-readable outputs for agent-facing surfaces;
- make ambiguity fail closed rather than inventing a value.

For multi-file work, finish one coherent dependency slice before widening the surface.

### 5. PROVE — verification is part of implementation

If Thea is installed, resolve the proof rather than recalling it:

```bash
thea gate <changed-file>
thea verify
```

For each changed surface, run the cheapest relevant proof first, then widen: parse/syntax;
formatter/lint; compiler/typecheck; targeted tests; required integration/build/security/performance
gates; repository-wide verification when required.

Judge commands by exit status, not reassuring output.

Classify each gate as **PASS**, **FAIL**, or **NOT RUN**. Never translate NOT RUN into PASS.

A task is done only when the requested artifact exists and its required gates pass, or when the
remaining blocker is explicitly reported.

### 6. LEARN — turn repeated failure into structure

When a check fails, a result is stale, a command was wrong, a guard misfires, or the user corrects
the work: fix the immediate cause; determine the failure shape; follow `skills/thea/SKILL.md`;
deduplicate against existing shapes; add or strengthen a guard when enforceable.

Do not compensate for a recurring failure with longer instructions when it can become a test,
schema, invariant, check or refusal.

### 7. COMPACT — collapse context without losing state

Compact after a coherent milestone, before a handoff, or whenever loaded context becomes mostly
historical.

Retain objective and constraints; changed paths/symbols; authoritative decisions by id/path; gate
verdicts and command identifiers; unresolved assumptions/blockers; exact next action.

Discard superseded hypotheses, resolved raw search output, unchanged file bodies, repeated
explanations, successful intermediate command chatter, rediscoverable tool descriptions, and prose
copies of repository facts.

A good compact state should let another capable agent resume without rereading the repository.

## Context budget

Use progressive disclosure:

- **Level 0 — task:** user request + local instructions.
- **Level 1 — route:** target, language/place, relevant gates, known lessons.
- **Level 2 — implementation:** exact source ranges + directly coupled tests/dependencies.
- **Level 3 — subsystem:** component interfaces/architecture only when Level 2 cannot resolve it.
- **Level 4 — codebase:** cross-layer map only for genuinely architectural work.

Never jump to Level 4 because the repository is unfamiliar. When tools expose structured JSON,
retain identifiers and verdicts instead of rendering large prose into context.

## Tool discipline

Choose tools by missing information: search to locate; fetch/read to understand a known target;
edit/write to change; shell/test to prove; git/diff to inspect effects; external research only when
repository state cannot answer the question.

Do not load every MCP, plugin, skill or tool manual. Discover capabilities on demand.

Before a destructive, privileged, external, costly or state-changing action, verify target and scope.
Do not infer permission from the ability to call a tool.

## Development modes

**Implement:** route → behavioral contract/tests → smallest owner → targeted gates → required wider
gates → compact.

**Debug:** reproduce → isolate boundary → one falsifiable hypothesis → minimum evidence → fix cause →
rerun reproducer → regression gate → ledger recurring shape.

**Refactor:** establish behavior-preserving proof first → restructure → prove behavior → measure
complexity/context improvement when that is the goal.

**Review:** diff first → route changed files → load only evidence needed → report concrete defects by
impact, each with evidence and the gate/test that exposes it. Do not invent findings to fill a quota.

**Plan:** map objective to responsible surfaces → resolve design-changing uncertainties first →
dependency-ordered implementation slices, each with proof.

**Handoff:** return machine-recoverable state, not narrative history:

```text
objective:
changed:
proof:
  PASS:
  FAIL:
  NOT_RUN:
decisions:
blockers:
next:
```

## Claim discipline

Use **CONFIRMED** for repository/tool evidence observed this run, **INFERRED** for a conclusion from
confirmed evidence, and **UNCERTAIN** when evidence is missing.

Commands, versions, APIs and file ownership recalled from memory are hypotheses until checked when
checking is available.

## Stop conditions

Stop expanding context when the responsible implementation surface is identified, behavior is
sufficiently specified, and required gates are known.

Stop editing when the requested change is complete, unrelated work would begin, or a missing
decision/permission blocks correctness.

Stop the task when required proof passes or a precise blocker and smallest next action are known.

## Completion report

Default to:

```text
Changed: <paths/symbols and outcome>
Proof: <PASS gates/commands>
Not run: <anything required but unavailable>
Risk: <remaining material uncertainty, or none>
```

Do not narrate every command. Output should describe the artifact and its proof.

## Thea integration

When available, treat Thea as authoritative for its own contract:
- `thea port` — minimum sufficient route/context;
- `thea plan` — task/change-class proof plan;
- `thea gate` — commands that prove a target;
- `thea failures --for` / `thea successes --for` — learned shapes/moves;
- `thea shell --json` — command interpretation safety;
- `thea verify` — final gate verdicts;
- branch landing flow — repository completion.

If Thea is absent, follow the same principles using the repository's native instructions and
toolchain. Never pretend Thea ran when it did not.
