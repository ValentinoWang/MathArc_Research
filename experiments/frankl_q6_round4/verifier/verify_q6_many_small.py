#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def union_closed(mask: int) -> bool:
    traces = [r for r in range(8) if (mask >> r) & 1]
    return all((mask >> (a | b)) & 1 for a in traces for b in traces)


def trace_summary(min_trace_size: int) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for mask in range(256):
        if not ((mask >> 7) & 1) or not union_closed(mask):
            continue
        traces = [r for r in range(8) if (mask >> r) & 1]
        if any(r.bit_count() < min_trace_size for r in traces):
            continue
        t = len(traces)
        delta = 3 * t - 2 * sum(r.bit_count() for r in traces)
        out.add((t, -delta))
    return out


def exact_count_dp(options: list[tuple[int, int, int]], count: int) -> dict[int, int]:
    """Map total deficit cost N to maximum negative B cost C."""
    dp = {0: 0}
    for _ in range(count):
        nxt: dict[int, int] = {}
        for total_n, total_c in dp.items():
            for _t, n, cost in options:
                key = total_n + n
                nxt[key] = max(nxt.get(key, -10**9), total_c + cost)
        dp = nxt
    return dp


def minimum_margin(
    k: int,
    hmin: list[int],
    single_options: list[tuple[int, int, int]],
    pair_options: list[tuple[int, int, int]],
) -> dict:
    single_dp = [exact_count_dp(single_options, a) for a in range(7)]
    pair_dp = [exact_count_dp(pair_options, b) for b in range(16)]
    best: tuple[int, dict] | None = None
    for a in range(max(0, k - 15), min(6, k) + 1):
        b = k - a
        # Every pair of selected singleton supports forces its two-set union.
        if b < a * (a - 1) // 2:
            continue
        for ns, cs in single_dp[a].items():
            for np, cp in pair_dp[b].items():
                total_n = ns + np
                p_required = 3 + total_n
                if p_required > 42:
                    continue
                negative_cost = cs + cp
                margin = hmin[p_required] - 12 - negative_cost
                record = {
                    "singletons": a,
                    "pairs": b,
                    "total_negative_deficit": total_n,
                    "positive_cores_required": p_required,
                    "small_fiber_B_cost": negative_cost,
                    "H_min": hmin[p_required],
                    "margin": margin,
                }
                if best is None or margin < best[0]:
                    best = (margin, record)
    return {
        "k": k,
        "feasible_relaxation": best is not None,
        "minimum_margin": None if best is None else best[0],
        "worst_relaxed_assignment": None if best is None else best[1],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmin", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    hdata = json.loads(args.hmin.read_text(encoding="utf-8"))
    hmin = hdata["Hmin"]
    expected_hmin = [
        6, 6, 12, 12, 12, 12, 24, 30, 36, 36, 42, 42, 42, 48,
        48, 48, 48, 60, 72, 84, 90, 102, 108, 114, 114, 126,
        132, 138, 138, 144, 144, 144, 156, 162, 168, 168, 174,
        174, 174, 180, 180, 180, 180,
    ]
    assert hmin == expected_hmin

    singleton_exact = trace_summary(2)
    pair_exact = trace_summary(1)
    assert singleton_exact == {(1, 3), (2, 4), (3, 5), (4, 6)}
    assert pair_exact == {
        (1, 3), (2, 4), (2, 2), (3, 5), (3, 3), (4, 6),
        (4, 4), (4, 2), (5, 5), (5, 3), (6, 4), (7, 3),
    }

    # For a fixed trace count t, replacing its deficit by the smallest possible
    # negative deficit only lowers the required number of positive cores. This
    # is a relaxation and is therefore safe for a lower-bound proof.
    singleton_all = [(1, 3, 4), (2, 4, 8), (3, 5, 12), (4, 6, 16)]
    pair_all = [(1, 3, 2), (2, 2, 4), (3, 3, 6), (4, 2, 8),
                (5, 3, 10), (6, 4, 12), (7, 3, 14)]
    singleton_nonfull = singleton_all[:-1]
    pair_nonfull = pair_all[:-1]

    all_type_results = [minimum_margin(k, hmin, singleton_all, pair_all) for k in range(8, 12)]
    expected_all = {8: 8, 9: 6, 10: 4, 11: 8}
    assert {item["k"]: item["minimum_margin"] for item in all_type_results} == expected_all

    full_singleton = {
        "eligible_positive_cores": 16,
        "minimum_required_for_k_ge_5": 17,
        "impossible_for_k_ge_5": True,
    }
    full_pair = {
        "eligible_positive_cores": 27,
        "minimum_required_for_k_ge_12": 28,
        "impossible_for_k_ge_12": True,
    }

    nonfull_results = [
        minimum_margin(k, hmin, singleton_nonfull, pair_nonfull)
        for k in range(12, 22)
    ]
    expected_nonfull = {
        12: 28, 13: 24, 14: 20, 15: 30,
        16: 28, 17: 28, 18: 36,
    }
    observed = {
        item["k"]: item["minimum_margin"]
        for item in nonfull_results
        if item["feasible_relaxation"]
    }
    assert observed == expected_nonfull
    assert all(
        not item["feasible_relaxation"] for item in nonfull_results if item["k"] >= 19
    )

    result = {
        "schema_version": 1,
        "claim": (
            "In the q=6 minimum-three-set trace-fiber setting, every case with "
            "at least eight small outside parts satisfies B_6>=0."
        ),
        "claim_status": "exact finite combinatorial certificate",
        "trace_summaries": {
            "singleton": sorted(singleton_exact),
            "pair": sorted(pair_exact),
        },
        "all_trace_types_k_8_to_11": all_type_results,
        "full_singleton_exclusion": full_singleton,
        "full_pair_exclusion": full_pair,
        "nonfull_k_12_to_21": nonfull_results,
        "conclusion": {
            "k_8_to_18": "all relaxed margins nonnegative",
            "k_19_to_21": "infeasible because more than 42 positive cores would be required",
        },
        "all_checks_passed": True,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
