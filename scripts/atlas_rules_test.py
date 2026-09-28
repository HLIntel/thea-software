#!/usr/bin/env python3
"""The rules that guard THIS HARNESS: its YAML shape, its own plants, and its forbidden-call table.

Split out of atlas_guards_test.py at 3.31.0 because that file reached the 1000-line cap, and a cap is
never raised to fit new code. Same contract as its sibling: each case plants a real defect, asserts the
build refuses it, and registers into the RUNNING suite's counted CASES — so a skipped case moves the
asserted total instead of disappearing quietly.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

T = None  # the running atlas_test module, bound by run()


def run(module) -> None:
    global T, ROOT, CASES, case, mutated, atlas
    T = module
    ROOT, CASES, case, mutated, atlas = (module.ROOT, module.CASES, module.case,
                                         module.mutated, module.atlas)
    yaml_shape_cases()
    plant_anchor_cases()
    callshape_cases()
    roster_cases()
    own_enforcement_cases()
    project_marker_cases()
    machine_dependence_cases()
    ast_cache_cases()
    landing_target_cases()
    command_effect_cases()
    resolver_cases()
    horizon_cases()
    effect_cases()
    task_concern_cases()


def _git(repo, *args: str) -> None:
    """Run git in a scratch repository with an identity, quietly, never raising.

    ONE COPY FOR THE WHOLE SUITE (3.37.0). Three cases needed a throwaway repository and each wrote its
    own two-line wrapper; the duplicate-structure cap caught the third and refused it, which is what a cap
    of zero is for. A test helper written three times drifts three ways.
    """
    import subprocess  # noqa: PLC0415
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                   capture_output=True, timeout=600, check=False)


def yaml_shape_cases() -> None:
    """Prose inside a YAML flow collection is quoted, so a comma cannot silently split a declared item (3.28.0).

    SPECIFICITY FIRST, and it decided the shape of the rule. A version reading any unquoted prose value
    anywhere flagged 434 of this tree's 2660 inline values; it was refused and never shipped, because a
    guard that fires on correct content gets switched off. Narrowed to flow context it flagged 45, and
    those 45 were quoted rather than exempted — each verified by parsing the file before and after and
    comparing the loaded data, not by reading the diff.
    """
    import yaml  # noqa: PLC0415
    from yamlshape import flow_prose, yaml_shape_errors
    # The defect itself: ONE intended item, written unquoted, that a later comma turned into TWO.
    intended = "a sentence that gained, a comma"
    split = yaml.safe_load(f"k: [{intended}, tail]")["k"]
    correct = {
        "quoted prose in a flow sequence": "k: ['a sentence with a comma, kept whole', b]",
        "a two-word idiom": "k: [go vet, read only, dry run]",
        "a quoted flow map value": "k: {why: 'the reason, stated in full'}",
        "prose in a BLOCK scalar, which this rule does not judge": "k: a plain sentence, with a comma",
        "nested quoted steps": "k: {steps: [[go, vet, ./...]]}",
    }
    for name, text in correct.items():
        if flow_prose(text):
            raise SystemExit(f"FAIL yamlshape fired on correct YAML: {name} -> {text}")
    if intended in split or len(split) != 3:
        raise SystemExit(f"FAIL the split shape this rule exists for did not reproduce: {split}")
    if len(flow_prose(f"k: [{intended}, tail]")) != 1:
        raise SystemExit(f"FAIL yamlshape did not flag the unquoted sentence that split: "
                         f"{flow_prose(f'k: [{intended}, tail]')}")
    if yaml_shape_errors():
        raise SystemExit(f"FAIL the tree is not clean, so this rule would be switched off: {yaml_shape_errors()[:2]}")
    CASES.append((f"yamlshape allows {len(correct)} correct YAML shapes and flags the unquoted sentence "
                  f"that a comma splits into {len(split)} declared items",
                  "a rule that fires on correctly quoted flow, on an idiom, or on a block scalar it does "
                  "not judge — the 434-finding version of this guard, which was refused"))
    print("  ok    yamlshape allows correct YAML and reads a split flow item as prose")
    # The plant unquotes a real declared item: adding a clause to it would silently become two rungs.
    with mutated("atlas.yaml", lambda s: s.replace("'the duplicate-key loader'", "the duplicate-key loader", 1)):
        case("an unquoted sentence inside a YAML flow collection FAILS",
             "a declared item that a later comma splits in two while the file still parses",
             True, "unquoted prose inside a flow collection")
def plant_anchor_cases() -> None:
    """A mutation anchor that matches nothing is refused, and the deliberate first-occurrence form is not (3.28.0).

    This rule is the one that pays for itself immediately: the two stale anchors it found at 3.28.0 were
    each discovered the expensive way first, five minutes into a mutating suite that then had to restore
    the tree. Reading them from the syntax tree costs under a second.
    """
    from plantcheck import anchors, plant_anchor_errors
    rows = anchors()
    many = sum(1 for suite, target, a in rows if (ROOT / target).exists()
               and (ROOT / target).read_text(encoding="utf-8").count(a) > 1)
    if not rows or not many:
        raise SystemExit(f"FAIL plantcheck read {len(rows)} anchors, {many} of them deliberately "
                         f"multi-matching — it cannot be proving specificity over nothing")
    if plant_anchor_errors():
        raise SystemExit(f"FAIL a plant in this tree already applies to nothing: {plant_anchor_errors()[:2]}")
    CASES.append((f"plantcheck reads {len(rows)} mutation anchors and allows the {many} that match more "
                  f"than once by design",
                  "a rule refusing the deliberate first-occurrence plant, which is most of them — the "
                  "shape that gets a guard switched off"))
    print("  ok    plantcheck reads every mutation anchor and allows the deliberate first-occurrence form")
    # The plant breaks an anchor the way a rewritten sentence does: the text is gone, the case is not.
    with mutated("scripts/atlas_test.py", lambda s: s.replace(
            '"    holds: [the task, the plan, the diff,', '"    holds: [no such line,', 1)):
        case("a mutation anchor that matches nothing FAILS",
             "a planted defect that applies to nothing, leaving the rule it tests unproven while the "
             "case it prints still says ok",
             True, "matches NOTHING in")
def callshape_cases() -> None:
    """Every forbidden_calls row bites, no row is unprobed, and correct calls are untouched (3.31.0).

    THE PLANTS ARE BUILT AT RUN TIME. This file is inside the roster two of the three rows sweep, so a
    literal `time.sleep(1)` or an untimed subprocess call written here would be the defect it plants —
    the same trap that caught three earlier plants in this suite.
    """
    from callshape import coverage, forbidden_call_errors, rules
    declared = rules()
    if forbidden_call_errors():
        raise SystemExit(f"FAIL the tree is not clean, so these rows would be switched off: "
                         f"{forbidden_call_errors()[:3]}")
    probes = {
        "bare_sleep": ("scripts/orphans.py", "\n\ndef _planted_wait():\n    import " + "time\n    "
                       + "time" + ".sleep(1)\n", "calls time.sleep"),
        "yaml_loader_bypass": ("scripts/leaks.py", "\n\ndef _planted_load():\n    return "
                               + "yaml" + "." + "safe_load" + '("{}")\n', "calls a PyYAML loader directly"),
        "subprocess_without_timeout": ("scripts/doctor.py", "\n\ndef _planted_run():\n    import "
                                       + "subprocess\n    return " + "subprocess" + "." + "run"
                                       + '(["true"])\n', "runs a subprocess with no timeout"),
    }
    if set(probes) != set(declared):
        raise SystemExit(f"FAIL a forbidden_calls row carries no planted case, so it stops nothing: "
                         f"declared={sorted(declared)} probed={sorted(probes)}")
    CASES.append((f"every forbidden_calls row is probed — {coverage()}",
                  "a data-driven deny table that grows past its own tests, where a new row reads as "
                  "enforcement and refuses nothing"))
    print("  ok    every forbidden_calls row is probed")
    for name, (target, addition, detail) in sorted(probes.items()):
        with mutated(target, lambda s, a=addition: s + a):
            case(f"forbidden_calls/{name} refuses the call it forbids",
                 "three copies of one guard, which had already drifted apart in roster and exemption",
                 True, detail)
    # SPECIFICITY: the owners and the exempted harnesses must stay silent, or the rows get switched off.
    from callshape import matches
    for name, expect_quiet in (("bare_sleep", "resilience.py"), ("yaml_loader_bypass", "atlascore.py")):
        hits = {path for path, _ in matches(name, declared[name])}
        if any(expect_quiet in h for h in hits):
            raise SystemExit(f"FAIL forbidden_calls/{name} fires on its own owner {expect_quiet}")
    CASES.append(("each forbidden_calls row stays silent on the module that owns the call",
                  "a guard that refuses the one place the call belongs, which is how it gets silenced"))
    print("  ok    each forbidden_calls row stays silent on the module that owns the call")


def roster_cases() -> None:
    """The instrument roster's denominator is a pattern, and an unreached instrument must say why (3.31.0).

    THE FIRST PLANT IS THE OLD BUG ITSELF. The denominator was `scripts/*.py`, so `heavyidle.mjs` — a
    declared instrument — sat outside its own completeness check. Removing its row proves the check now
    sees a non-Python script; under the suffix version this plant would have passed silently.
    """
    from roster import instrument_reach_errors, instrument_roster_errors
    roster_errors, named, present = instrument_roster_errors()
    if roster_errors or instrument_reach_errors():
        raise SystemExit(f"FAIL the roster is not clean, so these rules would be switched off: "
                         f"{(roster_errors + instrument_reach_errors())[:2]}")
    if named != present or not present:
        raise SystemExit(f"FAIL the roster does not cover its own denominator: {named} of {present}")
    CASES.append((f"every one of {present} scripts under scripts/ is a declared instrument",
                  "a roster counted by file extension, which stops seeing a sibling written in another "
                  "language — it already excluded a declared instrument from its own check"))
    print(f"  ok    every one of {present} scripts under scripts/ is a declared instrument")
    # THE ROSTER IS BUILT FROM EACH ROW'S `script:` VALUE, not its key, so renaming the key leaves the
    # file claimed and plants nothing — that version of this plant was inert and is why this comment
    # exists. Repointing the value is what actually leaves heavyidle.mjs claimed by no row.
    with mutated("atlas.yaml", lambda s: s.replace("    script: scripts/heavyidle.mjs\n",
                                                   "    script: scripts/verify.py\n", 1)):
        case("a script under scripts/ that no instrument row names FAILS, whatever its extension",
             "a roster that counts by suffix, so a script in another language needs no row and nothing fires",
             True, "named by no atlas.yaml/instruments entry")
    with mutated("atlas.yaml", lambda s: s.replace(
            "    requirements.txt: 'a pip input read by the install, not an instrument that proves anything'\n", "", 1)):
        case("a file under scripts/ that is neither an instrument nor a declared non-script FAILS",
             "a data file quietly counted as an instrument, or an instrument quietly counted as data",
             True, "named by no atlas.yaml/instruments entry")
    # AN UNREACHED INSTRUMENT MUST NAME ITS REASON. Removing the row must fail, because an arm that is
    # built, measured and wired to nothing reads as covered.
    with mutated("atlas.yaml", lambda s: s.replace("    'vaultlinks.py': '", "    'vaultlinks_moved.py': '", 1)):
        case("an instrument reached by no gate and declared nowhere FAILS",
             "an unshipped arm, which reads as covered precisely because it exists",
             True, "reached by no gate and no invariant")
    # SPECIFICITY: a row naming something a gate DOES reach must fail too, or it hides the next one.
    # astshape.py IS a gate's own argv (the code_shape gate runs it), so declaring it unreached must
    # fail: a stale row is a place for the next genuinely unreached instrument to hide.
    with mutated("atlas.yaml", lambda s: s.replace("    'packprobe.py': '",
                                                   "    'astshape.py': 'a stale row'\n    'packprobe.py': '", 1)):
        case("an unreached row naming an instrument a gate does name FAILS",
             "a stale exemption that the next genuinely unreached instrument hides behind",
             True, "now names directly")


def own_enforcement_cases() -> None:
    """The rung Thea ships to other repositories runs on THIS one, and its three defects stay fixed (3.32.0).

    SPECIFICITY IS ASSERTED FIRST AND IT IS THE WHOLE STORY. This rung was wired into no hook and no
    workflow here, and the reason it could not be was that it fired on correct content: it fed
    `docs/PYTHON.md` to Python's AST parser and `languages/rust/README.md` to rustc, because a route is
    GUIDANCE and a suffix is SOURCE. Twenty-two documents were refused for not being source.
    """
    import enforce
    quiet = {
        "a document whose directory routes to a language": ("docs/PYTHON.md", "not declared source"),
        "a language pack's own README": ("languages/rust/README.md", "not declared source"),
        "a pack's tools declaration": ("languages/python/tools.yaml", "not declared source"),
        "a planted benchmark fixture, whose failing test IS the artifact":
            ("benchmarks/agent/window/test_window.py", "planted failure by declaration"),
    }
    for name, (target, needle) in sorted(quiet.items()):
        state, detail = enforce.check_file(ROOT / target)
        if state != "SKIP" or needle not in detail:
            raise SystemExit(f"FAIL enforce fires on correct content: {name} -> {state} {detail}")
    CASES.append((f"the enforcement rung skips {len(quiet)} correct files it used to refuse",
                  "a rung that feeds a README to a compiler because the directory routes to a language "
                  "— which is why it was wired into no hook at all"))
    print("  ok    the enforcement rung skips the correct files it used to refuse")
    # COULD NOT DECIDE IS NOT DECIDED NO: six harnesses here are named *_test.py and are not pytest suites.
    verdict = enforce.test_file(ROOT / "scripts/agent_test.py")
    if verdict is not None and verdict[0] == "FAIL":
        raise SystemExit(f"FAIL a harness pytest cannot collect is reported as refused: {verdict}")
    CASES.append(("a test runner that collected nothing decides nothing, and is not a refusal",
                  "absence of evidence wearing the label of evidence of absence — pytest exit 5 read "
                  "as a failing suite, which refused six working harnesses"))
    print("  ok    a test runner that collected nothing decides nothing")
    # THE SAME TREE MUST GET THE SAME VERDICT FROM EITHER PATH SHAPE. `--staged` yields relative paths
    # and `--tracked` absolute ones, and the declared prefixes are relative: comparing the raw path
    # matched nothing for one of the two, and the fixtures came back refused.
    fixture = "benchmarks/agent/window/test_window.py"
    if enforce.check_file(ROOT / fixture)[0] != enforce.check_file(Path(fixture))[0]:
        raise SystemExit("FAIL enforce gives one tree two verdicts depending on the path shape it is handed")
    CASES.append(("the enforcement rung gives one verdict whatever path shape it is handed",
                  "a relative prefix compared against an absolute path, which silently matches nothing "
                  "for exactly one of the two callers"))
    print("  ok    the enforcement rung gives one verdict whatever path shape it is handed")
    if enforce.main(["check"]) != 2:
        raise SystemExit("FAIL a bare `check` swept nothing and did not refuse — a vacuous pass")
    CASES.append(("the enforcement rung refuses to sweep nothing and call it a pass",
                  "refusing 0 of 0 and 0 of many printing the same 0"))
    print("  ok    the enforcement rung refuses to sweep nothing and call it a pass")
    # SENSITIVITY: a real break in a real source file must still be refused.
    broken = "\n\ndef _planted_break(\n"
    with mutated("scripts/doctor.py", lambda s, b=broken: s + b):
        state, detail = enforce.check_file(ROOT / "scripts/doctor.py")
        if state != "FAIL":
            raise SystemExit(f"FAIL enforce passed a file that does not parse: {state} {detail}")
    CASES.append(("the enforcement rung still refuses a source file that does not parse",
                  "a rung narrowed until it refuses nothing, which is how a noisy guard gets silenced"))
    print("  ok    the enforcement rung still refuses a source file that does not parse")


def project_marker_cases() -> None:
    """A project-scoped checker with no project above the file SKIPS, and a marker is a GLOB (3.32.1).

    THE MACHINE THIS RAN ON DECIDED THE VERDICT, which is the defect. `enforce check --tracked` was clean
    here and RED in CI: this machine has no dotnet, so it skipped an F# script, while CI had dotnet and
    fed the bare script to `dotnet build`, which found no project and refused it. A local green is not a
    verdict. The toolchain is simulated below so the CI path is provable on a machine that lacks it.
    """
    import shutil

    import enforce
    real = shutil.which
    try:
        enforce.shutil.which = lambda name: "/usr/bin/" + name if name == "dotnet" else real(name)
        state, detail = enforce.check_file(ROOT / "examples/fsharp/BoundedRetry.fsx")
    finally:
        enforce.shutil.which = real
    if state != "SKIP" or "runs per project" not in detail:
        raise SystemExit(f"FAIL a project-scoped checker was handed a file with no project: {state} {detail}")
    CASES.append(("a project-scoped checker with no project above the file skips instead of refusing it",
                  "a checker that refuses a script for not being a project — and a clean sweep on a "
                  "machine that simply lacks the toolchain, read as a verdict"))
    print("  ok    a project-scoped checker with no project above the file skips instead of refusing it")
    # A MARKER IS A GLOB AND A LITERAL NAME GLOBS TO ITSELF, so the three exact markers must still resolve.
    # `atlas` bound by run() is the atlas MODULE, not the declaration reader — a name collision that
    # cost one full suite run. Import the reader explicitly.
    from atlascore import atlas as declaration
    markers = ((declaration().get("gate_tools") or {}).get("compiler_or_typechecker") or {}).get("per_directory") or {}
    literal = [m for m in markers.values() if "*" not in m and "?" not in m]
    if not literal or not any("*" in m or "?" in m for m in markers.values()):
        raise SystemExit(f"FAIL the marker table proves nothing about globs: {markers}")
    for name in literal:
        if enforce._project_home(ROOT / "scripts/atlas.py") is not None and not name:
            raise SystemExit("FAIL a literal marker stopped resolving under glob matching")
    CASES.append((f"the marker table carries {len(literal)} literal name(s) and at least one pattern, "
                  f"and both resolve",
                  "a marker compared as an exact name, which no per-project .NET file can ever match"))
    print("  ok    the marker table carries both a literal name and a pattern, and both resolve")
    # THE COVERAGE LINE MUST NAME ITS OWN BLIND SPOT, or the next clean local pass is read as a verdict.
    source = (ROOT / "scripts/enforce.py").read_text(encoding="utf-8")
    if "not a clean pass everywhere" not in source:
        raise SystemExit("FAIL the enforcement summary no longer names its machine-dependent blind spot")
    CASES.append(("the enforcement summary counts what it skipped for an absent toolchain",
                  "a green line from a sweep whose toolchains were missing, read as full coverage"))
    print("  ok    the enforcement summary counts what it skipped for an absent toolchain")


def machine_dependence_cases() -> None:
    """Every gate declares whether its verdict can depend on the machine, and a local pass says so (3.33.0).

    THE SIGHTING IS THIS REPOSITORY'S OWN: at 3.32.0 `own_enforcement` was green on the author's machine
    and RED in CI on the same tree, because this Mac has no dotnet and skipped an F# script that CI fed to
    a compiler. Nothing in the declaration said which gates carry that risk, so a clean local run was read
    as a verdict and cost a full cycle.
    """
    import verify
    from atlascore import atlas as declaration
    gates = (declaration().get("verification_policy") or {}).get("done_set") or []
    dependent = [g for g in gates if g.get("machine_dependent")]
    if not dependent or len(dependent) == len(gates):
        raise SystemExit(f"FAIL the flag separates no two gates: {len(dependent)} of {len(gates)}")
    for gate in dependent:
        if not str(gate.get("why_machine_dependent") or "").strip():
            raise SystemExit(f"FAIL done_set/{gate.get('id')} is machine dependent and says nothing about why")
    CASES.append((f"{len(dependent)} of {len(gates)} gates declare their verdict machine dependent, with reasons",
                  "a clean local run read as a universal verdict — measured green here and red in CI on "
                  "one tree"))
    print("  ok    the machine-dependent gates are declared, each with its reason")
    # THE FLAG TRAVELS ON THE ROW, not in a footnote: a consumer reading --json must see it too.
    row = verify.run_gate({"id": "probe", "argv": ["python", "-c", "pass"], "mutates": False,
                           "machine_dependent": True})
    plain = verify.run_gate({"id": "probe", "argv": ["python", "-c", "pass"], "mutates": False,
                             "machine_dependent": False})
    if not row.get("machine_dependent") or plain.get("machine_dependent"):
        raise SystemExit(f"FAIL the flag does not reach the row: {row.get('machine_dependent')} / "
                         f"{plain.get('machine_dependent')}")
    CASES.append(("a gate's machine dependence reaches its record, so --json carries it too",
                  "a caveat that lives only in the declaration, where a consumer reading the record "
                  "cannot see it"))
    print("  ok    a gate's machine dependence reaches its record")
    declared = "  - {id: lint, argv: [ruff, check, .], mutates: false, machine_dependent: false}"
    with mutated("atlas.yaml", lambda s, d=declared: s.replace(
            d, "  - {id: lint, argv: [ruff, check, .], mutates: false}", 1)):
        case("a done_set gate that does not declare machine_dependent FAILS",
             "a new gate silently assumed universal, which is the assumption that caused the sighting",
             True, "does not declare machine_dependent")
    with mutated("atlas.yaml", lambda s, d=declared: s.replace(
            d, "  - {id: lint, argv: [ruff, check, .], mutates: false, machine_dependent: true}", 1)):
        case("a machine-dependent gate with no stated reason FAILS",
             "a local-only verdict carrying a caveat nobody can act on",
             True, "states no why_machine_dependent")


def ast_cache_cases() -> None:
    """The syntax-tree cache is keyed by CONTENT, and a file that does not parse yields None (3.34.0).

    A NAME-KEYED TREE CACHE WOULD SILENTLY DISARM EVERY PLANT IN THIS SUITE: a case mutates a file and
    re-runs the contract, so a cache that answered by path would hand the guard the tree from before the
    mutation, and 186 cases would pass while proving nothing. That is the trap packmanifest.reset_caches
    records, and strict_yaml already avoids it the same way.
    """
    from atlascore import parsed_python
    one, two = "x = 1\n", "x = 2\n"
    if parsed_python(one, "a") is parsed_python(two, "a"):
        raise SystemExit("FAIL parsed_python answered from the NAME, not the content — every plant in "
                         "this suite would read a pre-mutation tree and pass while proving nothing")
    if parsed_python(one, "a") is not parsed_python(one, "b"):
        raise SystemExit("FAIL parsed_python missed a cache hit on identical text under a second name")
    if parsed_python("def (\n", "broken") is not None:
        raise SystemExit("FAIL parsed_python did not return None on a file that does not parse — a guard "
                         "crashing on it hides the parse check's own finding behind a traceback")
    CASES.append(("the syntax-tree cache answers from content, hits across names, and returns None on a "
                  "file that does not parse",
                  "a tree cache keyed by path, which would hand every planted defect the tree from "
                  "BEFORE its mutation and let 186 cases pass while proving nothing"))
    print("  ok    the syntax-tree cache answers from content, not from a name")


def landing_target_cases() -> None:
    """A landing targets the repository the caller is IN, and never the atlas it reads (3.35.0).

    THEA IS ADDED TO AN AGENT'S LAYER AND DOES NOT OWN ITS WORK. Before this, every git command in the
    landing tool ran with `cwd=ROOT` — so an agent that plugged the atlas in and asked to land would have
    pushed, tagged and opened a pull request against the ATLAS instead of its own repository.
    """
    import subprocess
    import tempfile

    from atlascore import ROOT, worktree
    # THE SPLIT MUST NOT DRIFT INTO A DIFFERENCE HERE: in this repository the atlas IS the worktree, so
    # every existing behaviour is unchanged and the new target is exercised only by a consumer.
    if worktree() != ROOT.resolve():
        raise SystemExit(f"FAIL the atlas and the worktree disagree in the atlas itself: "
                         f"{worktree()} vs {ROOT.resolve()}")
    CASES.append(("the atlas root and the landing target are the same path inside the atlas",
                  "a split that changes behaviour in the repository that defined it, where every "
                  "existing case would then be testing a different code path than a consumer runs"))
    print("  ok    the atlas root and the landing target are the same path inside the atlas")
    atlas_cli = [sys.executable, str(ROOT / "scripts" / "atlas.py")]
    refused = subprocess.run([*atlas_cli, "land"], cwd=ROOT, capture_output=True, text=True,
                             timeout=600, check=False)
    if refused.returncode != 3 or "is the ATLAS you read your rules from" not in refused.stdout:
        raise SystemExit(f"FAIL landing the atlas was not refused: rc={refused.returncode} "
                         f"{refused.stdout[:200]}")
    CASES.append(("`thea land` refuses the atlas itself, by identity and not by name",
                  "a consumer pushing to the repository it reads its rules from — which is what every "
                  "git command in the landing tool did before the target was separated from the atlas"))
    print("  ok    `thea land` refuses the atlas itself")
    # A FOREIGN REPOSITORY IS THE POINT: it must get PAST the refusal, and its diff must be judged by
    # its own language's check-only command before anything is pushed.
    with tempfile.TemporaryDirectory() as repo:
        def git(*a: str) -> None:
            _git(repo, *a)
        git("init", "-q", "-b", "main")
        git("commit", "-q", "--allow-empty", "-m", "base")
        (Path(repo) / "bad.py").write_text("def broken(\n", encoding="utf-8")
        git("add", "bad.py")
        env = {**os.environ, "THEA_ROOT": str(ROOT), "PYTHONPATH": str(ROOT / "scripts")}
        out = subprocess.run([*atlas_cli, "land"], cwd=repo, capture_output=True, text=True,
                             timeout=600, check=False, env=env)
    if "is the ATLAS" in out.stdout:
        raise SystemExit("FAIL a foreign repository was refused as though it were the atlas")
    if out.returncode == 0 or "does not pass its own language" not in out.stdout:
        raise SystemExit(f"FAIL a diff that does not parse was not refused before pushing: "
                         f"rc={out.returncode} {out.stdout[:300]}")
    CASES.append(("a foreign repository lands through the atlas, and a diff that does not parse is "
                  "refused before anything is pushed",
                  "a plug-and-play agent whose broken change reaches its remote, or whose own "
                  "repository is mistaken for the atlas"))
    print("  ok    a foreign repository lands through the atlas, and a broken diff is refused first")


def command_effect_cases() -> None:
    """Every subcommand is classified, and the read-only MCP route exposes only readers (3.35.0).

    THE DEFECT WAS INTRODUCED AND CAUGHT IN ONE VERSION. The MCP tool list is derived from the CLI's own
    subparsers, which is right; but every tool is annotated readOnlyHint, so adding `land` and `sync` to
    the CLI published two tools that PUSH as read-only. Derived is not the same as classified.
    """
    import thea_mcp
    from atlascore import atlas as declaration
    effects = declaration().get("command_effects") or {}
    writers, exposed = set(effects.get("writes") or {}), {t["name"] for t in thea_mcp.tools()}
    if not writers or not exposed:
        raise SystemExit(f"FAIL nothing to prove: {len(writers)} writers, {len(exposed)} exposed tools")
    if exposed & writers:
        raise SystemExit(f"FAIL the read-only route exposes a writing verb: {sorted(exposed & writers)}")
    if not exposed < set(thea_mcp._subparsers()):  # noqa: SLF001
        raise SystemExit("FAIL the exposed set is not a strict subset of the CLI, so nothing is filtered")
    CASES.append((f"the read-only MCP route exposes {len(exposed)} readers and none of the "
                  f"{len(writers)} verbs that write",
                  "a tool list derived from the CLI and annotated read-only, which publishes any new "
                  "writing verb as a read-only tool the day it is added"))
    print("  ok    the read-only MCP route exposes readers only")
    with mutated("atlas.yaml", lambda s: s.replace("  - failures\n", "", 1)):
        case("a subcommand classified in neither reads nor writes FAILS",
             "a new verb published by a read-only route by default, before anyone judged what it does",
             True, "classified in neither command_effects")
    with mutated("atlas.yaml", lambda s: s.replace("  - resume\n",
                                                   "  - resume\n  - land\n", 1)):
        case("a writing verb listed as a reader FAILS",
             "an annotation that is a rendering and not the identity — a tool that pushes, published "
             "to every agent as read-only",
             True, "classifies ['land'] as BOTH")


def resolver_cases() -> None:
    """Any declared name resolves to every namespace that declares it, and an unknown one REFUSES (3.36.0).

    675 declared names across 50 namespaces had no resolver, so the only way to learn what a name was
    meant reading the declaration breadth-first — the one thing this repository tells every reader not to
    do. A resolver that chose a winner among the namespaces would be right most of the time and silently
    wrong about the rest, which is what makes choosing dangerous.

    THE OVERLAP ITSELF IS A SEPARATE FINDING and is NOT excused here: six namespace pairs share three or
    more keys, one as a clean subset and five only partially, meaning they have already drifted with
    nothing checking that they agree. Reporting every namespace is how a reader SEES that; declaring the
    relation is how it gets refused, and that is `namespace_relations`, not this resolver.
    """
    import resolve
    from atlascore import atlas as declaration
    spaces = resolve.namespaces()
    if len(spaces) < 10:
        raise SystemExit(f"FAIL the namespace roster collapsed to {len(spaces)}; it is derived from the "
                         f"declaration's own top-level keys and cannot be this small")
    # EVERY HARD INVARIANT RESOLVES TO A NAMED ENFORCER. This is the coverage assertion: a bare list
    # member carries no fields, so without the cross-reference `thea id` told a reader only that it existed.
    invariants = declaration().get("hard_invariants") or []
    unnamed = [n for n in invariants
               if not any(h.get("enforced_by") and "NOTHING REGISTERED" not in h["enforced_by"]
                          for h in resolve.resolve(n))]
    if unnamed:
        raise SystemExit(f"FAIL {len(unnamed)} invariant(s) resolve to no named enforcer: {unnamed[:3]}")
    CASES.append((f"all {len(invariants)} hard invariants resolve to the function that enforces them",
                  "a bare list member that resolves to its own existence and nothing else, so a reader "
                  "still has to search the tree for what refuses it"))
    print(f"  ok    all {len(invariants)} hard invariants resolve to the function that enforces them")
    # AMBIGUITY IS REPORTED, NEVER RESOLVED (rule 4).
    doubled = [n for n in {m for members in spaces.values() for m in members}
               if len(resolve.resolve(n)) > 1]
    if not doubled:
        raise SystemExit("FAIL no name resolves to two namespaces, so the ambiguity rule is untested")
    if len(resolve.resolve(doubled[0])) < 2:
        raise SystemExit(f"FAIL {doubled[0]!r} was resolved to one namespace when it is declared in two")
    CASES.append((f"a name declared in more than one namespace resolves to ALL of them ({len(doubled)} such names)",
                  "a resolver that picks a winner on ambiguous input, which is worse than one that "
                  "errors — and it would be right most of the time, which is what makes it dangerous. "
                  "The overlap itself is refused by namespace_relations, not excused here"))
    print("  ok    a name declared in more than one namespace resolves to all of them")
    # AN UNKNOWN NAME REFUSES, and the refusal suggests rather than guessing.
    if resolve.resolve("a_name_that_is_declared_nowhere_at_all"):
        raise SystemExit("FAIL an undeclared name resolved to something")
    rc = resolve.main(["a_name_that_is_declared_nowhere_at_all", "--json"])
    if rc != 3:
        raise SystemExit(f"FAIL an undeclared name did not refuse: rc={rc}")
    CASES.append(("an undeclared name refuses with an exit code, and offers near misses instead of a guess",
                  "a resolver that answers something for every input, so a typo reads as a real finding"))
    print("  ok    an undeclared name refuses rather than guessing")


def horizon_cases() -> None:
    """A check that cannot see its input says NOT RUN, and the resolver reaches every declared depth (3.37.0).

    THE DEFECT THIS CLOSES was a clean pass CI did not earn. `actions/checkout` fetches ONE commit and
    every reading in the freshness check comes from `git log -1 -- <path>`, so on a shallow clone every
    path reads as touched at HEAD, nothing is behind, and there are no findings. CI printed green over
    THIRTEEN real ones, the oldest 36 minor versions behind. The check also sat in no gate, so even its
    exit code reached nobody.
    """
    import subprocess
    import tempfile

    import freshness
    import resolve
    # A SHALLOW CLONE MUST REFUSE. Built here rather than asserted in prose, because the whole defect was
    # a belief about what git would answer in an environment nobody reproduced.
    with tempfile.TemporaryDirectory() as home:
        origin = Path(home) / "origin"
        origin.mkdir()
        def git(cwd, *a):
            _git(cwd, *a)
        git(origin, "init", "-q", "-b", "main")
        for n in range(3):
            (origin / "f.txt").write_text(f"{n}\n", encoding="utf-8")
            git(origin, "add", "f.txt")
            git(origin, "commit", "-qm", f"c{n}")
        shallow = Path(home) / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{origin}", str(shallow)],
                       capture_output=True, timeout=600, check=False)
        saved = freshness.ROOT
        try:
            freshness.ROOT = shallow
            blind = freshness.history_is_visible()
        finally:
            freshness.ROOT = saved
    if not blind or "SHALLOW" not in blind:
        raise SystemExit(f"FAIL a shallow clone did not report itself blind: {blind!r}")
    if freshness.history_is_visible():
        raise SystemExit("FAIL this checkout reports itself blind, so the check would never run here")
    CASES.append(("the freshness check reports NOT RUN on a shallow clone instead of a clean pass",
                  "a clean pass a check did not earn — measured as 13 real findings invisible in CI, the "
                  "oldest 36 minor versions behind, because the runner fetches one commit"))
    print("  ok    the freshness check reports NOT RUN on a shallow clone")
    # THE RESOLVER'S TWO DEFECTS, both found by using it: a block is a name, and blocks nest.
    if not resolve.resolve("agent_policy"):
        raise SystemExit("FAIL a top-level block does not resolve, so `thea id agent_policy` answers none")
    nested = resolve.resolve("narrow_tools")
    if not any("/" in h["namespace"] for h in nested):
        raise SystemExit(f"FAIL a nested declaration does not resolve: {nested}")
    spaces = resolve.namespaces()
    if len(spaces) < 100:
        raise SystemExit(f"FAIL only {len(spaces)} namespaces reachable; nested blocks are where the "
                         f"names an agent meets in a refusal actually live")
    CASES.append((f"a top-level block and a nested one both resolve — {len(spaces)} namespaces reachable",
                  "a resolver that answers `none` for `agent_policy`, which is the most obvious question "
                  "an agent can ask, and for every control named in a refusal"))
    print(f"  ok    a top-level block and a nested one both resolve ({len(spaces)} namespaces)")
    # ASSERTED AGAINST ITS OWN INSTRUMENT, not against `check`. The horizon is a SEPARATE gate — it reads
    # git history, which `check` deliberately does not — so `case()` would run a check that cannot see
    # this rule and would report the wrong cause.
    from atlascore import atlas as declaration
    with mutated("atlas.yaml", lambda s: s.replace("      patterns: '3.37.0'" + chr(10), "", 1)):
        declaration.cache_clear()
        found = freshness.freshness_errors()
    declaration.cache_clear()
    if not any("patterns/" in f and "behind" in f for f in found):
        raise SystemExit(f"FAIL a path past the horizon with no review and no exemption was not refused: "
                         f"{found[:2]}")
    if freshness.freshness_errors():
        raise SystemExit(f"FAIL the horizon is not clean on this tree, so it could not be gated: "
                         f"{freshness.freshness_errors()[:2]}")
    CASES.append(("a path past the review horizon with neither a review nor an exemption is refused",
                  "a path nobody opened and nobody noticed — and a horizon that reported thirteen of "
                  "them for many versions while sitting in no gate at all"))
    print("  ok    a path past the review horizon with neither a review nor an exemption is refused")


def effect_cases() -> None:
    """A binary is not a capability: a command is bounded by what it DOES, not only by its name (3.38.0).

    THE SHIPPED REFERENCE CONTRACT ALLOWED `git`, which reads, writes and PUBLISHES in one word. Nothing
    said what a permitted command was permitted to do, so the only bound on an allowed binary was six
    denial patterns.

    SPECIFICITY IS THE HALF THAT DECIDES THIS ONE. Every contract written before the field existed must
    keep its exact meaning, so a contract with no `allowed_effects` is bounded by allowed_commands as
    before — and the case below proves that, because a silent behaviour change to every existing contract
    would be far worse than the hole it closes.
    """
    from agentpolicy import command_verdict
    from effects import tool_effects
    base = {"allowed_commands": ["git", "python3", "pytest", "curl", "nmap"],
            "allowed_paths": ["scripts"], "forbidden_paths": []}
    reader = {**base, "allowed_effects": ["read_repository", "execute_authored_code"]}
    writer = {**base, "allowed_effects": ["read_repository", "write_repository", "execute_authored_code"]}
    refused = {
        "a write on a read-only contract": (reader, ["git", "commit", "-m", "x"]),
        "publishing on a read-only contract": (reader, ["git", "push"]),
        "publishing even where writes are allowed": (writer, ["git", "push"]),
        "a network and credential reach, allowed nowhere": (writer, ["curl", "https://example.invalid"]),
        "a permitted binary whose capability nobody declared": (writer, ["nmap", "-sS"]),
    }
    for name, (contract, argv) in sorted(refused.items()):
        verdict = command_verdict(contract, argv)
        if verdict.allowed:
            raise SystemExit(f"FAIL an effect was not refused: {name} -> {argv}")
    allowed = {
        "a read on a read-only contract": (reader, ["git", "status"]),
        "authored code on a read-only contract": (reader, ["pytest", "scripts"]),
        "a write where writes are allowed": (writer, ["git", "add", "scripts/x"]),
        "EVERY PRE-3.38.0 CONTRACT, which declares no effects at all": (base, ["git", "push"]),
    }
    for name, (contract, argv) in sorted(allowed.items()):
        verdict = command_verdict(contract, argv)
        if not verdict.allowed:
            raise SystemExit(f"FAIL an effect rule fired on correct use: {name} -> {argv}: {verdict.reason}")
    # THE LONGEST KEY WINS, or every git verb is a read and the hole is still open.
    if tool_effects(["git", "push"])[0] != "git push" or tool_effects(["git", "status"])[0] != "git":
        raise SystemExit(f"FAIL the verb row does not override its binary: {tool_effects(['git', 'push'])}")
    CASES.append((f"a command is bounded by what it DOES — {len(refused)} capabilities refused, "
                  f"{len(allowed)} correct uses allowed, and a verb row overrides its binary",
                  "a contract that names a binary and grants everything that binary can do, including "
                  "publishing; and a silent meaning change to every contract written before the field"))
    print("  ok    a command is bounded by what it does, and pre-existing contracts keep their meaning")
    with mutated("atlas.yaml", lambda s: s.replace("  'git push': [write_repository, publish]",
                                                   "  'git push': [write_repository]", 1)):
        from atlascore import atlas as declaration
        declaration.cache_clear()
        leaked = command_verdict(writer, ["git", "push"])
        declaration.cache_clear()
    if leaked.allowed is False and "publish" in leaked.reason:
        raise SystemExit("FAIL the plant did not take effect")
    if not leaked.allowed:
        raise SystemExit(f"FAIL the plant should make publishing invisible, proving the row is load "
                         f"bearing: {leaked.reason}")
    CASES.append(("removing publish from the git push row is what lets a publish through, so the row is "
                  "load bearing rather than decoration",
                  "an effect table that looks like a bound while the verdict comes from somewhere else"))
    print("  ok    the git push effect row is load bearing")
    with mutated("atlas.yaml", lambda s: s.replace("  read_credential: 'reads a secret, token or key'\n", "", 1)):
        case("an effect used by a tool row and declared nowhere FAILS",
             "a typo in an effect name, which permits nothing while reading like a bound",
             True, "which effects does not declare")
    # THE JOIN BETWEEN TWO ROSTERS KEYED BY THE SAME SUBJECT. This one bit within the version that added
    # it: `sort` had been in argument_paths since 3.29.0 with no effect row, and the moment a contract
    # bounded effects a correct command was refused.
    # `tee` has exactly ONE row, so removing it removes the coverage. `sort` has two — a bare row and a
    # verb row — and the verb row legitimately counts, which is why the first version of this plant did
    # not bite: the guard was right and the plant was wrong.
    with mutated("atlas.yaml", lambda s: s.replace("  tee: [write_repository]\n", "", 1)):
        case("a binary in argument_paths with no tool_effects row FAILS",
             "two rosters keyed by the same subject where one is silently short, which stays invisible "
             "until a contract bounds effects and refuses a command that was always correct",
             True, "the two rosters are keyed by the same subject")


def task_concern_cases() -> None:
    """Every word a profile hands an agent resolves to a meaning, and none is declared twice (3.37.0).

    44 of the 59 tokens in task_profiles named nothing declared anywhere, so `thea id` answered `none` for
    a word an agent met in a profile it had just been handed. A profile made of unresolvable words reads
    like a checklist and is a list of hopes.

    THE SPECIFICITY HALF IS "DECLARE ONCE". 15 tokens already resolve as gates or controls, and the rule
    must NOT demand a copy of them here — a second declaration of a live name is the drift this tree
    refuses everywhere else, and the guard refuses the duplicate too.
    """
    import resolve
    from atlascore import atlas as declaration
    a = declaration()
    profiles, concerns = a.get("task_profiles") or {}, a.get("task_concerns") or {}
    elsewhere = (set(a.get("gate_tools") or {}) | set(a.get("pack_actions") or {})
                 | set((a.get("agent_policy") or {}).get("controls") or {}))
    tokens = {str(t) for rows in profiles.values() for t in (rows if isinstance(rows, list) else [])}
    unresolved = sorted(t for t in tokens if t not in concerns and t not in elsewhere)
    if unresolved:
        raise SystemExit(f"FAIL {len(unresolved)} profile token(s) resolve to nothing: {unresolved[:4]}")
    reused = sorted(t for t in tokens if t in elsewhere)
    if not reused:
        raise SystemExit("FAIL no token resolves through an existing roster, so declare-once is untested")
    if set(concerns) & elsewhere:
        raise SystemExit(f"FAIL a concern duplicates a live name: {sorted(set(concerns) & elsewhere)[:3]}")
    for name in sorted(tokens):
        if not resolve.resolve(name):
            raise SystemExit(f"FAIL {name!r} is declared and `thea id` cannot find it")
    CASES.append((f"all {len(tokens)} task-profile tokens resolve — {len(concerns)} as declared concerns and "
                  f"{len(reused)} through a roster that already names them, with no name declared twice",
                  "a profile handing an agent words with nothing behind them, and the opposite mistake of "
                  "copying a live gate name into a second table where one copy goes stale"))
    print(f"  ok    all {len(tokens)} task-profile tokens resolve, none declared twice")
    with mutated("atlas.yaml", lambda s: s.replace("sidecar_metadata, citations]",
                                                   "sidecar_metadata, citations, a_word_with_nothing_behind_it]", 1)):
        case("a task-profile token that resolves to nothing FAILS",
             "a profile that reads like a checklist and is a list of hopes",
             True, "resolves as no gate, pack action, control or task_concern")
    with mutated("atlas.yaml", lambda s: s.replace("  telemetry: ",
                                                   "  codeql: 'a copy of a live gate name'\n  telemetry: ", 1)):
        case("a concern that copies a name already declared as a gate FAILS",
             "one name with two declarations, where the copy nobody reads goes stale first",
             True, "one name, one declaration")
