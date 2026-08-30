#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import deque
from itertools import product
from pathlib import Path

FULL_TRACE_MASK = sum(1 << r for r in range(1, 8))
FULL_SINGLETON_TRACE_MASK = sum(1 << r for r in (3, 5, 6, 7))
CORES = [x for x in range(1, 64) if x.bit_count() >= 3]


def union_closed(mask: int) -> bool:
    traces = [r for r in range(8) if (mask >> r) & 1]
    return all((mask >> (a | b)) & 1 for a in traces for b in traces)


def trace_types(min_trace_size: int):
    result = []
    for mask in range(256):
        if not ((mask >> 7) & 1) or not union_closed(mask):
            continue
        traces = tuple(r for r in range(8) if (mask >> r) & 1)
        if any(r.bit_count() < min_trace_size for r in traces):
            continue
        t = len(traces)
        delta = 3 * t - 2 * sum(r.bit_count() for r in traces)
        result.append({"mask": mask, "traces": traces, "t": t, "delta": delta})
    return result


def join_mask(a: int, b: int) -> int:
    out = 0
    for r in range(8):
        if (a >> r) & 1:
            for q in range(8):
                if (b >> q) & 1:
                    out |= 1 << (r | q)
    return out


def add_core(state: int, core: int) -> int:
    out = state
    bits = state
    while bits:
        low = bits & -bits
        z = low.bit_length() - 1
        bits -= low
        out |= 1 << (z | core)
    return out


def core_charge(state: int) -> int:
    total = 6
    for z in range(64):
        if not ((state >> z) & 1):
            continue
        s = z.bit_count()
        if s >= 4:
            total += 3 * (2 * s - 6)
    if (state >> 63) & 1:
        total -= 6
    return total


def max_cores_under_charge(cap: int) -> dict:
    seen = {1}
    queue = deque([1])
    max_count = 0
    witness = 1
    while queue:
        state = queue.popleft()
        count = sum((state >> x) & 1 for x in CORES)
        if count > max_count:
            max_count = count
            witness = state
        for x in CORES:
            if (state >> x) & 1:
                continue
            nxt = add_core(state, x)
            if core_charge(nxt) <= cap and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return {"cap": cap, "states": len(seen), "max_core_count": max_count, "witness_state_hex": hex(witness)}


def shifted_state(state: int, small: int) -> int:
    out = 0
    bits = state
    while bits:
        low = bits & -bits
        z = low.bit_length() - 1
        bits -= low
        out |= 1 << (z | small)
    return out


def full_pair_charge(state: int, y: int) -> int:
    gy = shifted_state(state, y)
    total = 0
    for w in range(64):
        s = w.bit_count()
        if s < 4:
            continue
        multiplicity = 0
        if (state >> w) & 1:
            multiplicity = 3
        if (gy >> w) & 1:
            multiplicity = max(multiplicity, 7)
        total += (2 * s - 6) * multiplicity
    if not (((state | gy) >> 63) & 1):
        total += 6
    return total


def full_singleton_charge(state: int, y: int) -> int:
    gy = shifted_state(state, y)
    total = 0
    for w in range(64):
        s = w.bit_count()
        if s < 4:
            continue
        in_g = bool((state >> w) & 1)
        in_gy = bool((gy >> w) & 1)
        if in_g and in_gy:
            multiplicity = 5
        elif in_g:
            multiplicity = 3
        elif in_gy:
            multiplicity = 4
        else:
            multiplicity = 0
        total += (2 * s - 6) * multiplicity
    if not (((state | gy) >> 63) & 1):
        total += 6
    return total


def max_restricted_cores(cap: int, small: int, charge_fn) -> dict:
    eligible = [x for x in CORES if (x & small) != small]
    eligible_mask = sum(1 << x for x in eligible)
    seen = {1}
    queue = deque([1])
    max_count = 0
    witness = 1
    while queue:
        state = queue.popleft()
        count = (state & eligible_mask).bit_count()
        if count > max_count:
            max_count = count
            witness = state
        for x in eligible:
            if (state >> x) & 1:
                continue
            nxt = add_core(state, x)
            if charge_fn(nxt, small) <= cap and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return {"cap": cap, "states": len(seen), "max_eligible_core_count": max_count, "witness_state_hex": hex(witness)}


def h_lower(p: int) -> int:
    if p <= 6:
        return 24 if p == 6 else 12
    if p == 7:
        return 30
    if p <= 9:
        return 36
    if p <= 12:
        return 42
    if p <= 16:
        return 48
    return 60


def cost(kind: str, trace: dict) -> int:
    return (4 if kind == "singleton" else 2) * trace["t"]


def p_required(traces) -> int:
    return 3 - sum(item[1]["delta"] for item in traces)


def coarse_margin(traces) -> int:
    p = p_required(traces)
    need = 12 + sum(cost(kind, trace) for kind, trace in traces)
    return h_lower(p) - need


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    singleton = trace_types(2)
    pair = trace_types(1)
    assert len(singleton) == 8
    assert len(pair) == 45
    assert {(x["t"], x["delta"]) for x in singleton} == {(1, -3), (2, -4), (3, -5), (4, -6)}
    assert {(x["t"], x["delta"]) for x in pair} == {
        (1, -3), (2, -4), (2, -2), (3, -5), (3, -3), (4, -6),
        (4, -4), (4, -2), (5, -5), (5, -3), (6, -4), (7, -3)
    }

    core_results = [max_cores_under_charge(cap) for cap in [24, 30, 36, 42, 54]]
    assert {x["cap"]: x["max_core_count"] for x in core_results} == {24: 6, 30: 7, 36: 9, 42: 12, 54: 16}

    full_pair = max_restricted_cores(59, 0b000011, full_pair_charge)
    assert full_pair["max_eligible_core_count"] == 3
    full_singleton = max_restricted_cores(89, 0b000001, full_singleton_charge)
    assert full_singleton["max_eligible_core_count"] == 5

    exact_two_checked = 0
    exact_two_full_pair_routes = 0
    exact_two_min_coarse_margin = 10**9
    for s, q in product(singleton, pair):
        exact_two_checked += 1
        if q["mask"] == FULL_TRACE_MASK:
            exact_two_full_pair_routes += 1
            assert 12 + cost("singleton", s) + cost("pair", q) <= 60
        else:
            margin = coarse_margin((("singleton", s), ("pair", q)))
            exact_two_min_coarse_margin = min(exact_two_min_coarse_margin, margin)
            assert margin >= 0
    for q1, q2 in product(pair, repeat=2):
        exact_two_checked += 1
        if q1["mask"] == FULL_TRACE_MASK or q2["mask"] == FULL_TRACE_MASK:
            exact_two_full_pair_routes += 1
            assert 12 + cost("pair", q1) + cost("pair", q2) <= 60
        else:
            margin = coarse_margin((("pair", q1), ("pair", q2)))
            exact_two_min_coarse_margin = min(exact_two_min_coarse_margin, margin)
            assert margin >= 0

    ss_pair_checked = ss_pair_full_routes = 0
    ss_pair_min_margin = 10**9
    for s1, s2, q in product(singleton, singleton, pair):
        if join_mask(s1["mask"], s2["mask"]) & ~q["mask"]:
            continue
        ss_pair_checked += 1
        traces = (("singleton", s1), ("singleton", s2), ("pair", q))
        if q["mask"] == FULL_TRACE_MASK:
            ss_pair_full_routes += 1
            assert 12 + sum(cost(k, t) for k, t in traces) <= 60
        else:
            margin = coarse_margin(traces)
            ss_pair_min_margin = min(ss_pair_min_margin, margin)
            assert margin >= 0

    spp_checked = spp_full_pair_routes = spp_full_singleton_routes = 0
    spp_min_margin = 10**9
    for s, q1, q2 in product(singleton, pair, pair):
        spp_checked += 1
        traces = (("singleton", s), ("pair", q1), ("pair", q2))
        total_need = 12 + sum(cost(k, t) for k, t in traces)
        if q1["mask"] == FULL_TRACE_MASK or q2["mask"] == FULL_TRACE_MASK:
            spp_full_pair_routes += 1
            assert total_need <= 60
        elif s["mask"] == FULL_SINGLETON_TRACE_MASK:
            spp_full_singleton_routes += 1
            assert total_need <= 90
        else:
            margin = coarse_margin(traces)
            spp_min_margin = min(spp_min_margin, margin)
            assert margin >= 0

    ppp_checked = ppp_full_pair_routes = 0
    ppp_min_margin = 10**9
    for q1, q2, q3 in product(pair, repeat=3):
        ppp_checked += 1
        traces = (("pair", q1), ("pair", q2), ("pair", q3))
        total_need = 12 + sum(cost(k, t) for k, t in traces)
        if any(q["mask"] == FULL_TRACE_MASK for q in (q1, q2, q3)):
            ppp_full_pair_routes += 1
            assert total_need <= 60
        else:
            margin = coarse_margin(traces)
            ppp_min_margin = min(ppp_min_margin, margin)
            assert margin >= 0

    result = {
        "schema_version": 1,
        "claim": "For |Omega|=6 and a minimum three-set S, if all three elements of S are below half and at most three small outside parts occur, then B_6>=0.",
        "claim_status": "machine-checked candidate special-case theorem",
        "scope_warning": "This does not prove the q=6 branch with four or more small parts, the minimum-three-set theorem for all q, or Frankl's conjecture.",
        "trace_type_counts": {"singleton": len(singleton), "pair": len(pair)},
        "core_charge_enumeration": core_results,
        "derived_core_charge_thresholds": {"p>=7": 30, "p>=8": 36, "p>=10": 42, "p>=13": 48, "p>=17": 60},
        "full_pair_propagation": {"enumeration": full_pair, "conclusion": "four positive cores imply forced high-layer balance at least 60"},
        "full_singleton_propagation": {"enumeration": full_singleton, "conclusion": "six positive cores imply forced high-layer balance at least 90"},
        "exact_two": {"assignments_checked": exact_two_checked, "full_pair_routes": exact_two_full_pair_routes, "minimum_coarse_margin": exact_two_min_coarse_margin, "accepted": True},
        "exact_three": {
            "two_singletons_plus_forced_pair": {"compatible_assignments_checked": ss_pair_checked, "full_pair_routes": ss_pair_full_routes, "minimum_coarse_margin": ss_pair_min_margin},
            "one_singleton_two_pairs": {"assignments_checked": spp_checked, "full_pair_routes": spp_full_pair_routes, "full_singleton_routes": spp_full_singleton_routes, "minimum_coarse_margin": spp_min_margin},
            "three_pairs": {"assignments_checked": ppp_checked, "full_pair_routes": ppp_full_pair_routes, "minimum_coarse_margin": ppp_min_margin},
            "accepted": True,
        },
        "residual_obligation": "Any q=6 bridge failure must have at least four small outside parts.",
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
