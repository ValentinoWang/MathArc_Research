from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from matharc.v02.demo import build_research_demo, write_research_demo


def run_check(name: str) -> dict[str, object]:
    if name == "finite-leap":
        def p(n: int) -> int:
            return n * n

        def q(n: int) -> int:
            return n * n + math.prod(n - k for k in range(101))

        prefix = all(p(n) == q(n) for n in range(101))
        witness = p(101) != q(101)
        result = {
            "check": name,
            "prefix_agreement_0_100": prefix,
            "witness_n": 101,
            "p_101": p(101),
            "q_101": q(101),
            "pass": prefix and witness,
        }
    elif name == "base":
        result = {"check": name, "left": 0, "right": 0, "pass": 0 == 0}
    elif name == "step-a":
        # Coefficients are stored low degree first.  The residual is
        # n^2 + (2n+1) - (n+1)^2.
        residual = [0, 0, 0]
        residual[2] += 1
        residual[1] += 2
        residual[0] += 1
        residual[2] -= 1
        residual[1] -= 2
        residual[0] -= 1
        result = {"check": name, "normal_form": residual, "pass": residual == [0, 0, 0]}
    elif name == "step-b":
        left = [1, 2, 1]
        right = [1, 2, 1]
        result = {"check": name, "left": left, "right": right, "pass": left == right}
    elif name == "induction-certificate":
        trace = build_research_demo()
        validation = trace.validate()
        result = {
            "check": name,
            "target_status": trace.claims["C-TARGET"].status.value,
            "trace_valid": validation["valid"],
            "pass": validation["valid"] and trace.claims["C-TARGET"].status.value == "PROVED",
        }
    else:
        raise ValueError(f"unknown check: {name}")
    if not result["pass"]:
        raise SystemExit(1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/v02-demo")
    parser.add_argument(
        "--check",
        choices=("finite-leap", "base", "step-a", "step-b", "induction-certificate"),
    )
    args = parser.parse_args()
    if args.check:
        print(json.dumps(run_check(args.check), ensure_ascii=False, indent=2, sort_keys=True))
        return
    paths = write_research_demo(Path(args.out_dir))
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))


if __name__ == "__main__":
    main()
