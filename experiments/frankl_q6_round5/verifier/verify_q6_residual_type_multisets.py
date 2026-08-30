#!/usr/bin/env python3
"""Round-5 exact residual trace-type audit for the Frankl q=6 special case.

This verifier is intentionally scoped. It does NOT prove Frankl's full
conjecture. It independently audits the residual k=4..7 trace-type multisets
against the exact H_p table established by the round-4 positive-core verifier,
then checks the finite trace-superfamily and support-union repairs for the
remaining exceptional categories.

Pure standard-library Python.
"""
from __future__ import annotations

import itertools
import json
from collections import defaultdict

S = 0b111
OMEGA = (1 << 6) - 1

# Exact H_p table produced by round-4 verify_positive_core_hmin.cpp.
HMIN = [
    6, 6, 12, 12, 12, 12, 24, 30, 36, 36, 42, 42, 42, 48,
    48, 48, 48, 60, 72, 84, 90, 102, 108, 114, 114, 126,
    132, 138, 138, 144, 144, 144, 156, 162, 168, 168, 174,
    174, 174, 180, 180, 180, 180,
]
assert len(HMIN) == 43


def union_closed(mask: int) -> bool:
    traces = [r for r in range(8) if (mask >> r) & 1]
    return all((mask >> (a | b)) & 1 for a in traces for b in traces)


def trace_families() -> list[dict]:
    out = []
    for mask in range(256):
        if not ((mask >> S) & 1) or not union_closed(mask):
            continue
        traces = [r for r in range(8) if (mask >> r) & 1]
        t = len(traces)
        delta = 3 * t - 2 * sum(r.bit_count() for r in traces)
        out.append({
            "mask": mask,
            "traces": traces,
            "size": t,
            "delta": delta,
            "contains_empty": bool(mask & 1),
        })
    assert len(out) == 90
    return out


def allowed_trace_families(families: list[dict], outside_size: int) -> list[dict]:
    return [
        item
        for item in families
        if all(outside_size + r.bit_count() >= 3 for r in item["traces"])
    ]


def full_pair_shift_bound(p: int) -> int:
    return 14 * ((p + 2) // 3)


def top_fiber_correction(families: list[dict], slack: int) -> int:
    candidates = [item for item in families if -slack <= item["delta"] <= 0]
    minimum_size = min(item["size"] for item in candidates)
    empty_forced = all(item["contains_empty"] for item in candidates)
    if empty_forced:
        minimum_size = max(minimum_size, 3)
    return 6 * (minimum_size - 1)


def max_clique_size(adjacency: list[int]) -> int:
    best = 0

    def color_sort(vertices: int):
        order = []
        bounds = []
        color = 0
        remaining = vertices
        while remaining:
            color += 1
            available = remaining
            while available:
                bit = available & -available
                v = bit.bit_length() - 1
                order.append(v)
                bounds.append(color)
                remaining &= ~bit
                available &= ~bit
                available &= ~adjacency[v]
        return order, bounds

    def expand(vertices: int, size: int):
        nonlocal best
        if not vertices:
            best = max(best, size)
            return
        order, bounds = color_sort(vertices)
        for index in range(len(order) - 1, -1, -1):
            if size + bounds[index] <= best:
                return
            v = order[index]
            bit = 1 << v
            if vertices & bit:
                expand(vertices & adjacency[v], size + 1)
                vertices &= ~bit

    expand((1 << len(adjacency)) - 1, 0)
    return best


def low_positive_geometry_records(max_charge: int = 66) -> list[dict]:
    records = []
    triples = [x for x in range(64) if x.bit_count() == 3]
    fours = [x for x in range(64) if x.bit_count() == 4]
    fives = [x for x in range(64) if x.bit_count() == 5]

    for q_size in (3, 4, 5):
        q = (1 << q_size) - 1
        eligible = [x for x in range(1 << q_size) if x.bit_count() >= 3]
        q_index = eligible.index(q)
        for choose in range(1 << len(eligible)):
            if not ((choose >> q_index) & 1):
                continue
            family = {0} | {
                eligible[i]
                for i in range(len(eligible))
                if (choose >> i) & 1
            }
            if not all((a | b) in family for a in family for b in family):
                continue
            charge = 6 + sum(
                3 * (2 * x.bit_count() - 6)
                for x in family
                if x.bit_count() >= 4
            )
            if charge <= max_charge:
                records.append({
                    "charge": charge,
                    "top": False,
                    "capacity": len(family) - 1,
                })

    for number_fives in range(7):
        for number_fours in range(16):
            charge = 18 + 12 * number_fives + 6 * number_fours
            if charge > max_charge:
                continue
            for chosen_fives in itertools.combinations(fives, number_fives):
                for chosen_fours in itertools.combinations(fours, number_fours):
                    high = {OMEGA, *chosen_fives, *chosen_fours}
                    if not all((a | b) in high for a in high for b in high):
                        continue
                    allowed_triples = [
                        t
                        for t in triples
                        if all((t | h) in high for h in high)
                    ]
                    adjacency = [0] * len(allowed_triples)
                    for i, left in enumerate(allowed_triples):
                        for j in range(i + 1, len(allowed_triples)):
                            right = allowed_triples[j]
                            if (left | right) in high:
                                adjacency[i] |= 1 << j
                                adjacency[j] |= 1 << i
                    records.append({
                        "charge": charge,
                        "top": True,
                        "capacity": len(high) + max_clique_size(adjacency),
                    })
    return records


def union_size_of_edges(number_edges: int) -> int:
    edges = [
        (1 << a) | (1 << b)
        for a, b in itertools.combinations(range(6), 2)
    ]
    minimum = 7
    for chosen in itertools.combinations(edges, number_edges):
        union = 0
        for edge in chosen:
            union |= edge
        minimum = min(minimum, union.bit_count())
    return minimum


def audit() -> dict:
    families = trace_families()
    singletons = allowed_trace_families(families, 1)
    pairs = allowed_trace_families(families, 2)
    positive = [item for item in families if item["delta"] == 1]
    zero = [item for item in families if item["delta"] == 0]

    assert len(singletons) == 8
    assert len(pairs) == 45
    assert len(positive) == 6
    assert len(zero) == 17

    singleton_classes = sorted({(1, x["size"], x["delta"]) for x in singletons})
    pair_classes = sorted({(2, x["size"], x["delta"]) for x in pairs})
    records = low_positive_geometry_records()
    assert len(records) == 11625

    total_multisets = 0
    coarse_residual = 0
    unresolved_rows = []

    for k in range(4, 8):
        for number_singletons in range(k + 1):
            number_pairs = k - number_singletons
            if number_singletons > 6 or number_pairs > 15:
                continue
            for sm in itertools.combinations_with_replacement(
                singleton_classes, number_singletons
            ):
                for pm in itertools.combinations_with_replacement(
                    pair_classes, number_pairs
                ):
                    types = sm + pm
                    total_multisets += 1
                    deficit = -sum(item[2] for item in types)
                    p_min = 3 + deficit
                    if p_min > 42:
                        continue
                    negative_cost = sum((6 - 2 * item[0]) * item[1] for item in types)
                    target = 12 + negative_cost
                    base_bound = HMIN[p_min]
                    if (2, 7, -3) in types:
                        base_bound = max(base_bound, full_pair_shift_bound(p_min))
                    if base_bound >= target:
                        continue
                    coarse_residual += 1

                    for p_actual in range(p_min, 43):
                        h_bound = HMIN[p_actual]
                        if (2, 7, -3) in types:
                            h_bound = max(h_bound, full_pair_shift_bound(p_actual))
                        if h_bound >= target:
                            break
                        slack = p_actual - p_min
                        for record in records:
                            if record["capacity"] < p_actual or record["charge"] >= target:
                                continue
                            correction = 0 if record["top"] else top_fiber_correction(
                                families, slack
                            )
                            margin = record["charge"] + correction - target
                            if margin < 0:
                                unresolved_rows.append({
                                    "k": k,
                                    "types": tuple(types),
                                    "p_min": p_min,
                                    "p_actual": p_actual,
                                    "target": target,
                                    "charge": record["charge"],
                                    "top": record["top"],
                                    "margin": margin,
                                })

    assert total_multisets == 244068
    assert coarse_residual == 82
    assert len(unresolved_rows) == 38

    categories = defaultdict(list)
    for row in unresolved_rows:
        key = (
            row["k"], row["types"], row["p_actual"],
            row["charge"], row["top"],
        )
        categories[key].append(row)
    assert len(categories) == 8

    p2 = [x for x in pairs if x["size"] == 2 and x["delta"] == -2]
    p4 = [x for x in pairs if x["size"] == 4 and x["delta"] == -2]
    p5 = [x for x in pairs if x["size"] == 5 and x["delta"] == -3]
    p6 = [x for x in pairs if x["size"] == 6 and x["delta"] == -4]
    assert (len(p2), len(p4), len(p5), len(p6)) == (3, 3, 6, 3)

    def has_positive_superfamily(item):
        return any(item["mask"] & ~candidate["mask"] == 0 for candidate in positive)

    def minimum_zero_superfamily_size(item):
        candidates = [
            candidate["size"]
            for candidate in zero
            if item["mask"] & ~candidate["mask"] == 0
        ]
        return min(candidates) if candidates else None

    assert all(has_positive_superfamily(item) for item in p2)
    assert all(has_positive_superfamily(item) for item in p4)
    assert all(not has_positive_superfamily(item) for item in p5)
    assert all(not has_positive_superfamily(item) for item in p6)
    assert all(minimum_zero_superfamily_size(item) >= 6 for item in p5)
    assert all(minimum_zero_superfamily_size(item) >= 8 for item in p6)

    minimum_union_sizes = {
        5: union_size_of_edges(5),
        6: union_size_of_edges(6),
        7: union_size_of_edges(7),
    }
    assert minimum_union_sizes == {5: 4, 6: 4, 7: 5}

    repair_bounds = {
        "k5_all_p4": 4,
        "k6_contains_p5_zero": 6,
        "k6_contains_p5_outside": 10,
        "k6_contains_p6_zero": 10,
        "k6_contains_p6_outside": 12,
        "k7_contains_six_p4_positive": 8,
        "k7_contains_six_p4_outside": 16,
    }

    repaired = 0
    category_summaries = []
    for key, rows in sorted(categories.items(), key=str):
        k, types, p_actual, charge, top = key
        shortfall = max(-row["margin"] for row in rows)
        type_counts = defaultdict(int)
        for typ in types:
            type_counts[typ] += 1

        if k == 5:
            assert type_counts == {(2, 4, -2): 5}
            bound = repair_bounds["k5_all_p4"]
        elif k == 6 and type_counts.get((2, 6, -4), 0):
            bound = (
                repair_bounds["k6_contains_p6_zero"]
                if top else repair_bounds["k6_contains_p6_outside"]
            )
        elif k == 6 and type_counts.get((2, 5, -3), 0):
            bound = (
                repair_bounds["k6_contains_p5_zero"]
                if top else repair_bounds["k6_contains_p5_outside"]
            )
        elif k == 7:
            assert type_counts.get((2, 4, -2), 0) >= 6
            bound = (
                repair_bounds["k7_contains_six_p4_positive"]
                if top else repair_bounds["k7_contains_six_p4_outside"]
            )
        else:
            raise AssertionError((key, type_counts))

        assert bound >= shortfall, (key, shortfall, bound)
        repaired += len(rows)
        category_summaries.append({
            "k": k,
            "types": [list(item) for item in types],
            "p_actual": p_actual,
            "low_geometry_charge": charge,
            "top_present": top,
            "rows": len(rows),
            "maximum_shortfall": shortfall,
            "repair_lower_bound": bound,
        })

    assert repaired == 38

    return {
        "schema_version": 1,
        "status": "ACCEPT",
        "claim": (
            "The round-4 q=6 proof's residual k=4..7 trace-type space is "
            "exhaustively audited: all 244,068 multisets are either closed "
            "by H_p/top corrections or fall into eight finite categories whose "
            "trace-superfamily/support-union repairs cover every remaining shortfall."
        ),
        "scope": {
            "minimum_nonempty_member_size": 3,
            "outside_ground_set_size_q": 6,
            "small_part_counts": [4, 5, 6, 7],
            "full_frankl_conjecture": "NOT_CLAIMED",
        },
        "counts": {
            "trace_families": len(families),
            "singleton_trace_types": len(singletons),
            "pair_trace_types": len(pairs),
            "positive_trace_types": len(positive),
            "low_positive_geometries": len(records),
            "trace_type_multisets": total_multisets,
            "coarse_residual_multisets": coarse_residual,
            "unresolved_rows_before_exception_repair": len(unresolved_rows),
            "exception_categories": len(categories),
            "repaired_rows": repaired,
        },
        "minimum_union_sizes_for_distinct_pairs": minimum_union_sizes,
        "trace_superfamily_facts": {
            "p2_types": len(p2),
            "p4_types": len(p4),
            "p5_types": len(p5),
            "p6_types": len(p6),
            "p5_positive_superfamily_exists": False,
            "p5_min_zero_superfamily_size": 6,
            "p6_positive_superfamily_exists": False,
            "p6_min_zero_superfamily_size": 8,
        },
        "exception_categories": category_summaries,
        "claim_boundary": (
            "This is an independent residual-type audit of the existing round-4 "
            "machine-checked q=6 special-case proof. It is not an independent "
            "reimplementation of the entire proof pipeline and does not prove "
            "Frankl's full conjecture."
        ),
    }


def main():
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
