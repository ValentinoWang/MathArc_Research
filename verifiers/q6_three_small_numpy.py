#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

OMEGA_SIZE = 6
TOP = (1 << OMEGA_SIZE) - 1
POSITIVE_CORES = tuple(
    sorted(
        (mask for mask in range(1, 1 << OMEGA_SIZE) if mask.bit_count() >= 3),
        key=lambda mask: (mask.bit_count(), mask),
    )
)

ORBIT_WITNESSES: tuple[tuple[int, int, int], ...] = (
    (1, 2, 3),
    (1, 3, 5),
    (1, 3, 6),
    (1, 3, 12),
    (1, 6, 10),
    (1, 6, 24),
    (3, 5, 6),
    (3, 5, 9),
    (3, 5, 10),
    (3, 5, 24),
    (3, 12, 48),
)
EXPECTED_MINIMA = (0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 24)
CORE_WITNESSES: tuple[tuple[int, ...], ...] = (
    (7, 11, 13, 14, 19, 21, 25, 15, 23, 27, 29),
    (7, 11, 13, 14, 19, 21, 25, 15, 23, 27),
    (7, 11, 13, 14, 19, 21, 25, 15, 23, 27),
    (7, 11, 13, 14, 19, 21, 25, 15, 23, 27),
    (7, 11, 13, 14, 19, 21, 25, 15, 23, 27),
    (7, 11, 13, 14, 25, 26, 28, 15, 27, 29),
    (7, 11, 13, 14, 19, 15, 23, 27, 31),
    (7, 11, 13, 14, 19, 15, 23, 27, 31),
    (7, 11, 13, 14, 19, 15, 23, 27, 31),
    (7, 11, 13, 25, 26, 15, 27, 29, 31),
    (7, 11, 52, 56, 15, 60, 55, 59, 63),
)


def permute_mask(mask: int, permutation: tuple[int, ...]) -> int:
    result = 0
    for source in range(OMEGA_SIZE):
        if (mask >> source) & 1:
            result |= 1 << permutation[source]
    return result


def canonical_pattern(pattern: tuple[int, ...]) -> tuple[int, ...]:
    return min(
        tuple(sorted(permute_mask(mask, permutation) for mask in pattern))
        for permutation in itertools.permutations(range(OMEGA_SIZE))
    )


def enumerate_three_small_orbits() -> list[tuple[int, ...]]:
    parts = [1 << index for index in range(OMEGA_SIZE)] + [
        (1 << left) | (1 << right)
        for left in range(OMEGA_SIZE)
        for right in range(left + 1, OMEGA_SIZE)
    ]
    orbits: set[tuple[int, ...]] = set()
    for pattern in itertools.combinations(parts, 3):
        singletons = tuple(mask for mask in pattern if mask.bit_count() == 1)
        if not all(
            (left | right) in pattern
            for left, right in itertools.combinations(singletons, 2)
        ):
            continue
        orbits.add(canonical_pattern(pattern))
    return sorted(orbits)


def add_core(closure: int, core: int) -> int:
    result = closure
    remaining = closure
    while remaining:
        low = remaining & -remaining
        outside = low.bit_length() - 1
        remaining ^= low
        result |= 1 << (outside | core)
    return result


def closure_of(cores: tuple[int, ...]) -> int:
    closure = 1
    for core in cores:
        closure = add_core(closure, core)
    return closure


def translate(closure: int, small_part: int) -> int:
    result = 0
    remaining = closure
    while remaining:
        low = remaining & -remaining
        outside = low.bit_length() - 1
        remaining ^= low
        result |= 1 << (outside | small_part)
    return result


def verify_orbit(
    small_parts: tuple[int, int, int],
    expected_minimum: int,
    witness_cores: tuple[int, ...],
) -> dict[str, Any]:
    singleton_count = sum(mask.bit_count() == 1 for mask in small_parts)
    pair_count = 3 - singleton_count
    positive_core_count = 3 + 3 * singleton_count + 2 * pair_count
    if len(witness_cores) != positive_core_count:
        raise AssertionError("witness core count does not match the deficit bound")

    maxima = [4 if mask.bit_count() == 1 else 7 for mask in small_parts]
    penalties = np.array(
        [4 if mask.bit_count() == 1 else 2 for mask in small_parts],
        dtype=np.int16,
    )
    mesh = np.array(
        np.meshgrid(
            *[np.arange(1, maximum + 1, dtype=np.int16) for maximum in maxima],
            indexing="ij",
        )
    )
    trace_sizes = mesh.reshape(3, -1).T
    constants = (-12 - trace_sizes @ penalties).astype(np.int16)

    # State index = base-membership * 8 + translate-membership mask.
    multiplicities = np.zeros((len(trace_sizes), 16), dtype=np.int16)
    for base in range(2):
        for translate_mask in range(8):
            values = np.full(
                len(trace_sizes), 3 if base else 0, dtype=np.int16
            )
            for index in range(3):
                if (translate_mask >> index) & 1:
                    values = np.maximum(values, trace_sizes[:, index])
            multiplicities[:, base * 8 + translate_mask] = values

    @lru_cache(maxsize=None)
    def worst_margin(closure: int) -> int:
        translates = [translate(closure, part) for part in small_parts]
        generated = closure
        for translated in translates:
            generated |= translated
        weights = np.zeros(16, dtype=np.int16)
        for outside in range(1 << OMEGA_SIZE):
            outside_size = outside.bit_count()
            if outside_size < 4:
                continue
            translate_mask = sum(
                1 << index
                for index, translated in enumerate(translates)
                if (translated >> outside) & 1
            )
            base = (closure >> outside) & 1
            if base or translate_mask:
                weights[base * 8 + translate_mask] += 2 * outside_size - 6
        top_bonus = 0 if (generated >> TOP) & 1 else 6
        values = constants + top_bonus + multiplicities @ weights
        return int(values.min())

    witness_margin = worst_margin(closure_of(witness_cores))
    if witness_margin != expected_minimum:
        raise AssertionError(
            f"witness margin {witness_margin} != {expected_minimum}"
        )

    nodes = [0] * (positive_core_count + 1)
    pruned = [0] * (positive_core_count + 1)
    chosen = [0] * positive_core_count
    counterexample: dict[str, Any] | None = None

    def dfs(start: int, depth: int, closure: int) -> None:
        nonlocal counterexample
        nodes[depth] += 1
        current = worst_margin(closure)
        if current >= expected_minimum:
            pruned[depth] += 1
            return
        if depth == positive_core_count:
            counterexample = {"margin": current, "cores": chosen.copy()}
            return
        need = positive_core_count - depth
        last = len(POSITIVE_CORES) - need
        for core_index in range(start, last + 1):
            core = POSITIVE_CORES[core_index]
            child = add_core(closure, core)
            if worst_margin(child) < current:
                raise AssertionError("monotone lower-bound regression")
            chosen[depth] = core
            dfs(core_index + 1, depth + 1, child)
            if counterexample is not None:
                return

    dfs(0, 0, 1)
    return {
        "small_parts": list(small_parts),
        "singleton_count": singleton_count,
        "pair_count": pair_count,
        "selected_positive_cores": positive_core_count,
        "trace_size_maxima": maxima,
        "exact_minimum": expected_minimum,
        "witness_cores": list(witness_cores),
        "counterexample_below_minimum": counterexample,
        "nodes_by_depth": nodes,
        "pruned_by_depth": pruned,
        "cached_closures": worst_margin.cache_info().currsize,
        "status": "PASS" if counterexample is None else "FAIL",
    }


def verify_three_small_parts() -> dict[str, Any]:
    enumerated_orbits = enumerate_three_small_orbits()
    if enumerated_orbits != list(ORBIT_WITNESSES):
        raise AssertionError(
            f"orbit classification mismatch: {enumerated_orbits}"
        )
    results = [
        verify_orbit(pattern, minimum, witness)
        for pattern, minimum, witness in zip(
            ORBIT_WITNESSES, EXPECTED_MINIMA, CORE_WITNESSES
        )
    ]
    return {
        "schema_version": 1,
        "theorem_id": "FRANKL-Q6-EXACTLY-THREE-SMALL-OUTSIDE-PARTS",
        "claim": (
            "In the minimum-three-set q=6 trace-fiber setup, if exactly three "
            "small outside parts occur and all three elements of S are below half, "
            "then B_6 >= 0."
        ),
        "claim_boundary": (
            "This closes exactly three small outside parts only. It does not close "
            "four-or-more small parts, the full q=6 bridge, or Frankl's conjecture."
        ),
        "orbit_count": len(enumerated_orbits),
        "orbits": [list(item) for item in enumerated_orbits],
        "positive_core_count_rule": "p >= 3 + 3r + 2e",
        "results": results,
        "exact_minima": list(EXPECTED_MINIMA),
        "certified_global_lower_bound_for_subcase": min(EXPECTED_MINIMA),
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "new_residual": (
            "Any q=6 outside-balance counterexample must have at least four "
            "small outside parts."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify_three_small_parts()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(args.output),
                "new_residual": report["new_residual"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
