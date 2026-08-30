from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
from collections.abc import Iterable
from pathlib import Path

EXPECTED_NON_SMT_SKIP_IDS = frozenset(
    {
        "unittest.loader.ModuleSkipped.tests.test_api_stream",
        "unittest.loader.ModuleSkipped.tests.test_codex_agent",
    }
)


def _flatten(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            assert isinstance(item, unittest.TestCase)
            yield item


def _is_smt_test(test_id: str) -> bool:
    return "test_v02_smt_tools" in test_id


def authoritative_smt_gate(
    *,
    z3_available: bool,
    smt_discovered: int,
    smt_executed: int,
    smt_skipped: int,
) -> tuple[str, ...]:
    """Return exact reasons an SMT result cannot serve as authoritative Gate 0."""

    failures: list[str] = []
    if not z3_available:
        failures.append("z3 is unavailable; SMT coverage would be skipped")
    if smt_discovered <= 0:
        failures.append("no SMT tests were discovered")
    if smt_executed <= 0:
        failures.append("no SMT tests actually executed")
    if smt_skipped > 0:
        failures.append(f"{smt_skipped} SMT tests were skipped")
    return tuple(failures)


def authoritative_non_smt_skip_gate(
    actual_skip_ids: Iterable[str],
    *,
    expected_skip_ids: frozenset[str] = EXPECTED_NON_SMT_SKIP_IDS,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return missing and unexpected non-SMT skip IDs for authoritative Gate 0."""

    actual = frozenset(actual_skip_ids)
    missing = tuple(sorted(expected_skip_ids - actual))
    unexpected = tuple(sorted(actual - expected_skip_ids))
    return missing, unexpected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-dir", default="tests")
    parser.add_argument("--pattern", default="test*.py")
    parser.add_argument("--summary-path", default="artifacts/ci/unittest-summary.json")
    parser.add_argument("--require-z3", action="store_true")
    args = parser.parse_args(argv)

    suite = unittest.defaultTestLoader.discover(
        start_dir=args.start_dir,
        pattern=args.pattern,
        top_level_dir=".",
    )
    test_ids = [test.id() for test in _flatten(suite)]
    smt_ids = [test_id for test_id in test_ids if _is_smt_test(test_id)]
    z3_available = importlib.util.find_spec("z3") is not None

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    skipped = [(test.id(), reason) for test, reason in result.skipped]
    smt_skipped = [item for item in skipped if _is_smt_test(item[0])]
    non_smt_skipped_ids = sorted(
        {test_id for test_id, _reason in skipped if not _is_smt_test(test_id)}
    )
    missing_non_smt_skips, unexpected_non_smt_skips = authoritative_non_smt_skip_gate(
        non_smt_skipped_ids
    )
    smt_executed = len(smt_ids) - len(smt_skipped)

    summary = {
        "tests_discovered": len(test_ids),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
        "z3_available": z3_available,
        "smt_tests_discovered": len(smt_ids),
        "smt_tests_skipped": len(smt_skipped),
        "smt_tests_executed": smt_executed,
        "expected_non_smt_skip_ids": sorted(EXPECTED_NON_SMT_SKIP_IDS),
        "actual_non_smt_skip_ids": non_smt_skipped_ids,
        "missing_non_smt_skip_ids": list(missing_non_smt_skips),
        "unexpected_non_smt_skip_ids": list(unexpected_non_smt_skips),
        "skipped_tests": [
            {"test_id": test_id, "reason": reason} for test_id, reason in skipped
        ],
    }
    output = Path(args.summary_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("\n=== MathArc unittest Gate 0 summary ===")
    print(
        "tests: discovered={tests_discovered} run={tests_run} failures={failures} "
        "errors={errors} skipped={skipped}".format(**summary)
    )
    print(
        "SMT: z3_available={z3_available} discovered={smt_tests_discovered} "
        "executed={smt_tests_executed} skipped={smt_tests_skipped}".format(**summary)
    )
    print(
        "non-SMT skip whitelist: expected={expected_non_smt_skip_ids} "
        "actual={actual_non_smt_skip_ids} missing={missing_non_smt_skip_ids} "
        "unexpected={unexpected_non_smt_skip_ids}".format(**summary)
    )
    if skipped:
        print("Skipped tests:")
        for test_id, reason in skipped:
            print(f"- {test_id}: {reason}")
    print(f"machine_summary: {output}")

    if not result.wasSuccessful():
        return 1
    if args.require_z3:
        failures = list(
            authoritative_smt_gate(
                z3_available=z3_available,
                smt_discovered=len(smt_ids),
                smt_executed=smt_executed,
                smt_skipped=len(smt_skipped),
            )
        )
        if missing_non_smt_skips:
            failures.append(
                "expected non-SMT skips disappeared: " + ", ".join(missing_non_smt_skips)
            )
        if unexpected_non_smt_skips:
            failures.append(
                "unexpected non-SMT skips appeared: "
                + ", ".join(unexpected_non_smt_skips)
            )
        if failures:
            print("AUTHORITATIVE GATE FAIL: test coverage differs from the frozen contract.")
            for failure in failures:
                print(f"- {failure}")
            return 2
    elif not z3_available:
        print(
            "DEGRADED PASS ONLY: z3 unavailable. This result may be useful for development "
            "but is not authoritative Gate 0 green evidence."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
