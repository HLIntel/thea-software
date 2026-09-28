#!/usr/bin/env python3
"""A command is bounded by what it DOES, not only by its name.

WHY (3.36.0). A task contract named BINARIES, and a binary is not a capability: the shipped reference
contract allowed `git`, which reads, writes AND publishes in one word. `denied_commands` catches a few
shapes by pattern and `argument_paths` adjudicates where a command writes; nothing said what a permitted
command was permitted to DO.

Split out of agentpolicy.py because that file reached its 1000-line cap, and a cap is never raised to fit
new code. The separation is also honest: agentpolicy decides a contract's five controls, and this decides
capability, which is a different question about the same argv.

WHAT IT DOES NOT PROVE. That a command whose effects are allowed is CORRECT, or that an agent asks at all
— an agent that never calls the policy is bounded by its host. And it knows nothing about a capability no
row declares, which is exactly why an opted-in contract refuses that case instead of assuming it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from atlascore import atlas

if TYPE_CHECKING:
    from agentpolicy import Verdict


def _verdict():
    """Verdict lives in agentpolicy, which imports THIS module — so the import is deferred rather than
    duplicating the type, because two definitions of one type disagree the first time one is edited."""
    from agentpolicy import Verdict  # noqa: PLC0415
    return Verdict


def policy_effects() -> dict:
    """atlas.yaml/tool_effects — the roster of command shapes and what each is permitted to DO."""
    return dict(atlas().get("tool_effects") or {})

def tool_effects(argv: list[str]) -> tuple[str, list[str]] | None:
    """(the matching key, its effects) for this command shape, or None when no row declares it.

    LONGEST KEY WINS, so `git push` overrides `git` rather than repeating it. Matching only the binary
    would make every git verb a read, which is how `allowed_commands: [git]` came to grant publishing.
    """
    if not argv:
        return None
    rows = policy_effects()
    binary = argv[0].rsplit("/", 1)[-1]
    for width in (2, 1):
        key = " ".join([binary, *argv[1:width]]) if width > 1 else binary
        if key in rows:
            return key, [str(e) for e in rows[key] or []]
    return None

def effect_verdict(contract: dict, argv: list[str]) -> Verdict | None:
    """The capability refusal a command earns from what it DOES, or None when it earns none.

    WHY. A contract named binaries, and a binary is not a capability: the shipped reference contract
    allowed `git`, which reads, writes AND publishes. Nothing said what a permitted command was permitted
    to do, so the only bound on a permitted binary was the denied_commands patterns.

    AN OPT-IN THAT FAILS CLOSED. A contract without `allowed_effects` is bounded by allowed_commands
    exactly as before, so every contract written earlier keeps its meaning. A contract WITH it refuses any
    shape that has no row in tool_effects, because the safe answer for a capability nobody declared is no.
    """
    allowed = contract.get("allowed_effects")
    if allowed is None:
        return None
    permitted = {str(e) for e in allowed}
    found = tool_effects(argv)
    if found is None:
        return _verdict()(False, "narrow_tools",
                       f"{(argv[0] if argv else '')!r} declares no effects in atlas.yaml/tool_effects, and "
                       f"this contract bounds effects — an undeclared capability is refused, not assumed")
    key, effects = found
    if not effects:
        return _verdict()(False, "narrow_tools",
                       f"tool_effects/{key} declares an EMPTY effect list, which reads as harmless and was "
                       f"never decided; state what it does")
    over = sorted(set(effects) - permitted)
    if over:
        return _verdict()(False, "narrow_tools",
                       f"{key!r} has effect(s) {over} that this contract does not allow "
                       f"(allowed_effects: {sorted(permitted)})")
    return _verdict()(True, "narrow_tools", f"{key!r} needs {sorted(effects)}, all allowed")
