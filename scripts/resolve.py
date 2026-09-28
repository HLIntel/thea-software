#!/usr/bin/env python3
"""`thea id <name>` — what is this name, where is it declared, and what enforces it.

WHY (3.36.0). An agent meets a name everywhere: in a refusal, a commit message, a generated document,
another agent's handoff. Nothing could answer "what IS this" without reading the declaration
breadth-first, which is the one thing this repository tells every reader not to do. `route` answers it
for a PATH and `failures` for one ledger shape; 675 declared names across 50 namespaces had no resolver
at all.

IT REPORTS EVERY NAMESPACE A NAME APPEARS IN, and never picks one. A resolver that chose a winner would
be right most of the time and silently wrong about the rest, which is worse than one that errors (rule 4).

AND THE OVERLAP IS A FINDING, NOT A FEATURE. MEASURED at 3.36.0: 35 names are declared in more than one
namespace, and six PAIRS of namespaces share three or more keys. One of those six is a clean subset —
every language with an example runner is a language, so the runner map is a VIEW of the roster. The other
five overlap only PARTIALLY, which means they have already drifted apart, and nothing in this tree checks
that they agree. Two parallel maps keyed by the same subject are a join nobody declared: add a member to
one and the other is silently short. The relation between two overlapping namespaces belongs in the
declaration, and `namespace_relations` is where it goes.

THE NAMESPACE ROSTER IS DERIVED from the declaration's own top-level keys, so a block added tomorrow is
searchable without a line here. An enumerated list would narrow the day a namespace landed beside it.

WHAT IT DOES NOT PROVE. That the thing is correct, or reachable — `verify` and the instrument roster
answer those. This answers where to look, which is the question that was costing a breadth-first read.
"""
from __future__ import annotations

import json
import re
import sys

from atlascore import ROOT, atlas

# The fields worth printing when a declared value carries them: what it claims, who refuses it, and why.
TELLING = ("proves", "does_not_prove", "closed_by", "enforced_by", "prevented_by", "unenforceable",
           "shape", "why", "refuses", "role", "script", "message", "reason", "when", "returns")


MAX_DEPTH = 3   # measured: depth 3 reaches every nested block an agent asked about; 4 adds only noise


def namespaces(node: object = None, trail: str = "", depth: int = 0) -> dict[str, object]:
    """Every declaration block whose members are named, at ANY declared depth. DERIVED, never listed.

    NESTED BLOCKS ARE WHERE THE ANSWERS LIVE (3.37.0). The first version read only the top level, so the
    change classes under `verification_policy/profiles`, the five controls under `agent_policy/controls`
    and the severities under `verification_policy/severity` all resolved to `none` — and those are
    precisely the names an agent meets in a refusal. MEASURED by using the resolver to review three prose
    areas: of 57 identifiers they name, 41 read as undeclared at depth 1 and 26 at depth 2, almost all of
    them the tool's fault rather than the documents'.
    """
    found: dict[str, object] = {}
    node = atlas() if node is None else node
    if depth > MAX_DEPTH or not isinstance(node, dict):
        return found
    for key, value in node.items():
        if not isinstance(key, str):
            continue
        path = f"{trail}/{key}" if trail else key
        if isinstance(value, dict) and value and all(isinstance(k, str) for k in value):
            found[path] = value
            found.update(namespaces(value, path, depth + 1))
        elif isinstance(value, list) and value and all(isinstance(x, str) for x in value):
            found[path] = value
    return found


def _block_line(name: str) -> int:
    """The line a top-level block is declared on, so a reader can jump straight to it."""
    lines = (ROOT / "atlas.yaml").read_text(encoding="utf-8").splitlines()
    return next((i + 1 for i, line in enumerate(lines) if line.startswith(f"{name}:")), 1)


def declared_at(namespace: str, name: str) -> str:
    """`atlas.yaml:<line>` for a name INSIDE its namespace's block, or the block itself when the member
    is on a flow line. Scoped to the block, because the same word appears many times in a 3,000-line
    declaration and the first hit is usually the wrong one."""
    lines = (ROOT / "atlas.yaml").read_text(encoding="utf-8").splitlines()
    leaf = namespace.rsplit("/", 1)[-1]
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(f"{namespace}:") or line.strip() == f"{leaf}:"), None)
    if start is None:
        return "atlas.yaml"
    member = re.compile(rf"^\s+(-\s+)?'?{re.escape(name)}'?\s*:?\s*($|[#'\"\[{{]|.*)")
    for i in range(start + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace() and not lines[i].startswith("#"):
            break                                   # left the block
        if member.match(lines[i]):
            return f"atlas.yaml:{i + 1}"
    return f"atlas.yaml:{start + 1}"


def resolve(name: str) -> list[dict]:
    """Every declaration of `name`: the block it names, and every namespace it is a member of.

    A NAMESPACE IS A DECLARED NAME TOO (3.37.0). The first version resolved only MEMBERS, so
    `thea id agent_policy` answered `none` for a block with nine members — a false refusal on the most
    obvious question an agent can ask. Found by using the resolver to review three prose areas: 41 of the
    57 identifiers they name read as undeclared, and the tool was wrong about almost all of them.
    """
    hits: list[dict] = []
    spaces = namespaces()
    if name in atlas():
        members = spaces.get(name)
        block = atlas()[name]
        hits.append({"id": name, "namespace": "(top level)", "declared_at": f"atlas.yaml:{_block_line(name)}",
                     "kind": f"{type(block).__name__} of {len(block)} entr(y/ies)" if hasattr(block, "__len__")
                             else type(block).__name__,
                     "members": sorted(members)[:12] if members else []})
    for namespace, members in sorted(namespaces().items()):
        if name not in members:
            continue
        value = members[name] if isinstance(members, dict) else None
        record = {"id": name, "namespace": namespace, "declared_at": declared_at(namespace, name),
                  "kind": type(value).__name__ if value is not None else "member"}
        if isinstance(value, dict):
            record["fields"] = {f: value[f] for f in TELLING if f in value}
        elif value is not None:
            record["value"] = value
        record.update(_cross_reference(namespace, name))
        hits.append(record)
    return hits


def _cross_reference(namespace: str, name: str) -> dict:
    """What a bare name cannot say for itself: the function that enforces it, the file that runs it.

    A member of a LIST namespace carries no fields at all — `hard_invariants` is 42 bare names — so
    resolving one told a reader it existed and nothing else. The enforcing function is knowable and lives
    in a registry, so it is looked up rather than restated in the declaration, where a second copy would
    go stale first (surface-and-structure §3).
    """
    if namespace == "hard_invariants":
        try:
            import atlasinv  # noqa: PLC0415
        except ImportError:
            return {}
        fn = atlasinv.INVARIANT_CHECKS.get(name)
        if fn is None:
            return {"enforced_by": "NOTHING REGISTERED — atlasinv.INVARIANT_CHECKS has no entry, which "
                                   "the contract refuses"}
        named = getattr(fn, "enforcer", None)          # a wrapper names what it wraps
        if named:
            return {"enforced_by": named}
        module = getattr(fn, "__module__", "") or ""
        return {"enforced_by": f"{module}.{getattr(fn, '__qualname__', fn.__name__)}".lstrip(".")}
    if namespace == "instruments":
        return {"run_with": f"python {(atlas().get('instruments') or {}).get(name, {}).get('script', '')}"}
    return {}


def near(name: str, limit: int = 6) -> list[str]:
    """Names that share a prefix or contain the query — a refusal that suggests beats one that does not."""
    everything = {n for members in namespaces().values() for n in members} | set(atlas())
    lowered = name.lower()
    return sorted({n for n in everything if lowered in n.lower() or n.lower() in lowered})[:limit]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    names = [a for a in args if not a.startswith("-")]
    if not names:
        print(f"usage: thea id <name> [--json]   ·   "
              f"{sum(len(m) for m in namespaces().values())} names over {len(namespaces())} namespaces")
        return 2
    hits = resolve(names[0])
    if as_json:
        print(json.dumps({"schema": 1, "command": "id", "query": names[0], "hits": hits,
                          "near": [] if hits else near(names[0])}, indent=2, default=str))
        return 0 if hits else 3
    if not hits:
        suggestions = near(names[0])
        print(f"none: {names[0]!r} is declared in no namespace of atlas.yaml")
        print("  did you mean: " + ", ".join(suggestions) if suggestions else
              "  nothing in the declaration resembles it")
        return 3
    for hit in hits:
        print(f"{hit['namespace']}/{hit['id']}   {hit['declared_at']}")
        for field, value in (hit.get("fields") or {}).items():
            print(f"    {field:<16} {str(value)[:110]}")
        if "value" in hit:
            print(f"    {'value':<16} {str(hit['value'])[:110]}")
        for field in ("enforced_by", "run_with"):
            if field in hit:
                print(f"    {field:<16} {hit[field]}")
        if hit.get("members"):
            print(f"    {'members':<16} {', '.join(hit['members'])}"
                  f"{' ...' if len(hit['members']) == 12 else ''}")
    if len(hits) > 1:
        print(f"\n{len(hits)} namespaces declare {names[0]!r}. That is not an error: the same subject is "
              f"often declared twice for different purposes, so every one is reported and none is chosen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
