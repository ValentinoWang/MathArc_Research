from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable

S_BITS = 3
OMEGA_BITS = 6
TOP = (1 << OMEGA_BITS) - 1
EMPTY_CLOSURE = 1
SELECTED_POSITIVE_CORES = 7


def popcount(value: int) -> int:
    return value.bit_count()


def trace_profiles(outside_size: int) -> dict[str, Any]:
    """Enumerate admissible nonempty trace fibers over a minimum three-set.

    A trace R is admissible only when |outside| + |R| >= 3, because S is a
    minimum-cardinality nonempty member. Every nonempty fiber contains the
    full trace S, and each fiber is union-closed.
    """
    if outside_size not in {1, 2}:
        raise ValueError("outside_size must be 1 or 2")
    full_trace = (1 << S_BITS) - 1
    allowed = {
        trace
        for trace in range(1 << S_BITS)
        if outside_size + popcount(trace) >= S_BITS
    }
    families: list[tuple[int, ...]] = []
    profiles: set[tuple[int, int]] = set()
    for family_bits in range(1 << (1 << S_BITS)):
        family = {
            trace
            for trace in range(1 << S_BITS)
            if (family_bits >> trace) & 1
        }
        if full_trace not in family or not family.issubset(allowed):
            continue
        if any((left | right) not in family for left in family for right in family):
            continue
        ordered = tuple(sorted(family))
        families.append(ordered)
        size = len(family)
        deficit = 3 * size - 2 * sum(popcount(trace) for trace in family)
        profiles.add((size, deficit))
    return {
        "outside_size": outside_size,
        "family_count": len(families),
        "profiles": [list(item) for item in sorted(profiles)],
        "maximum_size": max(len(item) for item in families),
        "maximum_deficit": max(
            3 * len(item) - 2 * sum(popcount(trace) for trace in item)
            for item in families
        ),
    }


@dataclass(frozen=True)
class Geometry:
    name: str
    y1: int
    y2: int
    outside_size_1: int
    outside_size_2: int
    expected_minimum: int
    witness_cores: tuple[int, ...]

    @property
    def t1_max(self) -> int:
        return 4 if self.outside_size_1 == 1 else 7

    @property
    def t2_max(self) -> int:
        return 4 if self.outside_size_2 == 1 else 7

    @property
    def penalty1(self) -> int:
        return 6 - 2 * self.outside_size_1

    @property
    def penalty2(self) -> int:
        return 6 - 2 * self.outside_size_2


GEOMETRIES: tuple[Geometry, ...] = (
    Geometry(
        "nested_singleton_pair",
        0b000001,
        0b000011,
        1,
        2,
        0,
        (7, 11, 13, 14, 15, 23, 31),
    ),
    Geometry(
        "disjoint_singleton_pair",
        0b000001,
        0b000110,
        1,
        2,
        0,
        (7, 11, 13, 14, 15, 45, 47),
    ),
    Geometry(
        "intersecting_pairs",
        0b000011,
        0b000101,
        2,
        2,
        6,
        (7, 11, 13, 14, 15, 23, 31),
    ),
    Geometry(
        "disjoint_pairs",
        0b000011,
        0b001100,
        2,
        2,
        6,
        (7, 11, 13, 14, 15, 23, 31),
    ),
)


POSITIVE_CORES: tuple[int, ...] = tuple(
    sorted(
        (mask for mask in range(1, 1 << OMEGA_BITS) if popcount(mask) >= 3),
        key=lambda mask: (popcount(mask), mask),
    )
)


def add_core(closure: int, core: int) -> int:
    """Adjoin one core to an already union-closed bitset of outside parts."""
    result = closure
    remaining = closure
    while remaining:
        low = remaining & -remaining
        outside = low.bit_length() - 1
        result |= 1 << (outside | core)
        remaining ^= low
    return result


def closure_of(cores: Iterable[int]) -> int:
    closure = EMPTY_CLOSURE
    for core in cores:
        closure = add_core(closure, core)
    return closure


def translate(closure: int, outside_part: int) -> int:
    result = 0
    remaining = closure
    while remaining:
        low = remaining & -remaining
        outside = low.bit_length() - 1
        result |= 1 << (outside | outside_part)
        remaining ^= low
    return result


def margin_for_sizes(closure: int, geometry: Geometry, t1: int, t2: int) -> int:
    """Coarse exact lower bound for B_6 from seven positive cores.

    The base fiber contributes -12. The two small fibers contribute
    -(6-2|Y_i|)t_i. A generated high fiber W has at least three traces if
    W lies in the positive-core union closure and at least t_i traces if it
    lies in the translate by Y_i. All omitted fibers have nonnegative
    B_6 coefficient. If the top is not generated, its unavoidable full-S
    trace contributes six.
    """
    if not (1 <= t1 <= geometry.t1_max and 1 <= t2 <= geometry.t2_max):
        raise ValueError("trace-fiber size outside the admissible coarse range")
    translated_1 = translate(closure, geometry.y1)
    translated_2 = translate(closure, geometry.y2)
    generated = closure | translated_1 | translated_2
    total = 0 if (generated >> TOP) & 1 else 6
    for outside in range(1 << OMEGA_BITS):
        outside_size = popcount(outside)
        if outside_size < 4:
            continue
        multiplicity = 0
        if (closure >> outside) & 1:
            multiplicity = max(multiplicity, 3)
        if (translated_1 >> outside) & 1:
            multiplicity = max(multiplicity, t1)
        if (translated_2 >> outside) & 1:
            multiplicity = max(multiplicity, t2)
        total += multiplicity * (2 * outside_size - 6)
    return total - 12 - geometry.penalty1 * t1 - geometry.penalty2 * t2


@lru_cache(maxsize=None)
def _worst_margin_cached(closure: int, geometry_name: str) -> tuple[int, int, int]:
    geometry = next(item for item in GEOMETRIES if item.name == geometry_name)
    best = 10**9
    best_t = (0, 0)
    for t1 in range(1, geometry.t1_max + 1):
        for t2 in range(1, geometry.t2_max + 1):
            margin = margin_for_sizes(closure, geometry, t1, t2)
            if margin < best:
                best = margin
                best_t = (t1, t2)
    return best, best_t[0], best_t[1]


def worst_margin(closure: int, geometry: Geometry) -> tuple[int, int, int]:
    return _worst_margin_cached(closure, geometry.name)


def classify_two_small_geometries() -> dict[str, Any]:
    """Record the four S_6-orbits; two distinct singleton parts are impossible."""
    return {
        "two_singletons": {
            "possible_with_exactly_two_small_parts": False,
            "reason": (
                "The union of two distinct singleton outside parts is a pair, "
                "and cross-fiber union closure makes that pair a third small part."
            ),
        },
        "remaining_orbits": [item.name for item in GEOMETRIES],
    }


def verify_geometry(geometry: Geometry) -> dict[str, Any]:
    """Prove that the coarse lower-bound functional never drops below its witness.

    The lower bound is monotone when another positive core is adjoined. Hence a
    node can be pruned once its current worst margin reaches the target minimum.
    """
    threshold, witness_t1, witness_t2 = worst_margin(
        closure_of(geometry.witness_cores), geometry
    )
    if threshold != geometry.expected_minimum:
        raise AssertionError(
            f"witness mismatch for {geometry.name}: {threshold} != {geometry.expected_minimum}"
        )
    nodes = [0] * (SELECTED_POSITIVE_CORES + 1)
    pruned = [0] * (SELECTED_POSITIVE_CORES + 1)
    counterexample: dict[str, Any] | None = None
    chosen = [0] * SELECTED_POSITIVE_CORES

    def dfs(start: int, depth: int, closure: int) -> None:
        nonlocal counterexample
        if counterexample is not None:
            return
        nodes[depth] += 1
        current_margin, current_t1, current_t2 = worst_margin(closure, geometry)
        if current_margin >= threshold:
            pruned[depth] += 1
            return
        if depth == SELECTED_POSITIVE_CORES:
            counterexample = {
                "margin": current_margin,
                "t": [current_t1, current_t2],
                "cores": chosen.copy(),
            }
            return
        need = SELECTED_POSITIVE_CORES - depth
        last = len(POSITIVE_CORES) - need
        for index in range(start, last + 1):
            core = POSITIVE_CORES[index]
            child = add_core(closure, core)
            child_margin, _, _ = worst_margin(child, geometry)
            if child_margin < current_margin:
                raise AssertionError(
                    f"monotonicity failure in {geometry.name}: "
                    f"{child_margin} < {current_margin}"
                )
            chosen[depth] = core
            dfs(index + 1, depth + 1, child)
            if counterexample is not None:
                return

    dfs(0, 0, EMPTY_CLOSURE)
    return {
        "geometry": geometry.name,
        "outside_parts": [geometry.y1, geometry.y2],
        "outside_sizes": [geometry.outside_size_1, geometry.outside_size_2],
        "trace_size_ranges": [[1, geometry.t1_max], [1, geometry.t2_max]],
        "exact_minimum": threshold,
        "witness_margin": threshold,
        "witness_t": [witness_t1, witness_t2],
        "witness_cores": list(geometry.witness_cores),
        "counterexample_below_minimum": counterexample,
        "nodes_by_depth": nodes,
        "pruned_by_depth": pruned,
        "status": "PASS" if counterexample is None else "FAIL",
    }


def verify_two_small_outside_parts() -> dict[str, Any]:
    singleton = trace_profiles(1)
    pair = trace_profiles(2)
    if singleton["profiles"] != [[1, -3], [2, -4], [3, -5], [4, -6]]:
        raise AssertionError("singleton trace profile regression")
    expected_pair = [
        [1, -3], [2, -4], [2, -2], [3, -5], [3, -3], [4, -6],
        [4, -4], [4, -2], [5, -5], [5, -3], [6, -4], [7, -3],
    ]
    if pair["profiles"] != expected_pair:
        raise AssertionError("pair trace profile regression")
    results = [verify_geometry(geometry) for geometry in GEOMETRIES]
    passed = all(item["status"] == "PASS" for item in results)
    return {
        "schema_version": 1,
        "theorem_id": "FRANKL-Q6-EXACTLY-TWO-SMALL-OUTSIDE-PARTS",
        "claim": (
            "In the minimum-three-set q=6 trace-fiber setup, if exactly two "
            "small outside parts occur and all three elements of S are below half, "
            "then B_6 >= 0."
        ),
        "claim_boundary": (
            "This closes exactly two small outside parts. It does not close "
            "three-or-more small parts, the full q=6 bridge, or Frankl's conjecture."
        ),
        "trace_profiles": {"singleton": singleton, "pair": pair},
        "positive_deficit_count": {
            "singleton_pair_minimum": 8,
            "pair_pair_minimum": 7,
            "selected_for_coarse_bound": SELECTED_POSITIVE_CORES,
            "derivation": "D>=3, singleton deficit<=-3, pair deficit<=-2",
        },
        "geometry_classification": classify_two_small_geometries(),
        "positive_core_count": len(POSITIVE_CORES),
        "results": results,
        "certified_global_lower_bound_for_subcase": min(
            item["exact_minimum"] for item in results
        ),
        "status": "PASS" if passed else "FAIL",
        "new_residual": (
            "Any q=6 outside-balance counterexample must have at least "
            "three small outside parts."
        ),
    }
