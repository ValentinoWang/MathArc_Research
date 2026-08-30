from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import compare_agents, load_results
from .budget import BudgetLedger
from .campaign import ResearchCampaign
from .claude_code_runtime import ClaudeCodeConfig, ClaudeCodeRunner, claude_code_status
from .demo import write_research_demo
from .failure_memory import FailureMemory
from .metrics import compute_research_metrics
from .model_workers import LLMProposalWorker
from .orchestrator import ResearchOrchestrator
from .review import (
    NominationError,
    ReviewAuthorizationError,
    ReviewContractError,
    ReviewDecision,
    ReviewerRoster,
    ReviewRecord,
    nominate_for_review,
    nominations_for_claim,
    review_to_evidence,
    revoke_review,
    reviews_for_claim,
    set_reviewer_roster,
    submit_review,
)
from .review_bundle import (
    AttackHistoryItem,
    ReviewBundleError,
    build_review_bundle,
    check_bundle_copy,
    render_review_bundle_html,
    write_review_bundle,
)
from .trace import load_trace, save_trace

DEFAULT_RUN_WALL_SECONDS_BUDGET = 30.0 * 60.0
DEFAULT_RUN_ROUNDS = 10


def _write_or_print(payload: object, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _build_run_budget(args: argparse.Namespace) -> BudgetLedger | None:
    """Build the fail-closed default campaign budget.

    Autonomous model loops must be bounded unless the operator explicitly
    opts out.  An explicit cost limit does not silently disable the default
    wall-clock limit; operators who truly want an unbounded run must pass
    --no-budget, which cannot be combined with any numeric budget flag.
    """

    if bool(args.no_budget):
        if args.wall_seconds_budget is not None or args.cost_usd_budget is not None:
            raise SystemExit(
                "--no-budget cannot be combined with --wall-seconds-budget or "
                "--cost-usd-budget"
            )
        return None
    wall_limit = (
        float(args.wall_seconds_budget)
        if args.wall_seconds_budget is not None
        else DEFAULT_RUN_WALL_SECONDS_BUDGET
    )
    if wall_limit <= 0:
        raise SystemExit("--wall-seconds-budget must be positive")
    if args.cost_usd_budget is not None and float(args.cost_usd_budget) <= 0:
        raise SystemExit("--cost-usd-budget must be positive")
    return BudgetLedger(
        wall_seconds_limit=wall_limit,
        cost_usd_limit=(
            float(args.cost_usd_budget) if args.cost_usd_budget is not None else None
        ),
    )


def _run_review_command(args: argparse.Namespace) -> None:
    """v0.3-review R3 CLI submission path (nominate/bundle/submit/revoke/status).

    Scope decision, made explicit rather than silently narrowed: this
    operates on the same bare-trace load_trace/save_trace round trip every
    other `matharc.v02` subcommand already uses (`run`, `plan`, ... none of
    them go through `ResearchWorkspace`/`SecuredResearchWorkspace`). The R3
    spec text asks for "对象级 can_review + RolePolicy 双检、封链" (object-
    level authorization *and* role-based policy, sealed into the hash-
    chained event ledger). Object-level `can_review` is fully enforced here
    -- it is `submit_review`'s own authority, not optional. `RolePolicy` and
    `EventLedger` sealing are deferred to when this is wrapped by
    `SecuredResearchWorkspace`, which is R6's job (the HTTP write path is
    explicitly coordinated with the workspace/server integration in the
    spec's own dependency line); retrofitting that heavier layer onto only
    the review subcommands, while every other v0.2/v0.3 CLI command stays
    bare-trace, would be an inconsistent design choice this session should
    not make unilaterally.
    """

    command = args.review_command
    if command == "nominate":
        trace = load_trace(args.trace)
        try:
            nomination = nominate_for_review(trace, args.claim)
        except NominationError as exc:
            save_trace(trace, args.trace)
            _write_or_print({"nominated": False, "reasons": list(exc.reasons)}, args.output)
            raise SystemExit(1)
        save_trace(trace, args.trace)
        _write_or_print({"nominated": True, **nomination.to_dict()}, args.output)
        return

    if command == "bundle":
        trace = load_trace(args.trace)
        attack_history: tuple[AttackHistoryItem, ...] = ()
        if args.attack_history:
            raw = json.loads(Path(args.attack_history).read_text(encoding="utf-8"))
            attack_history = tuple(AttackHistoryItem.from_dict(item) for item in raw)
        try:
            bundle = build_review_bundle(
                trace, args.claim, bundle_id=args.bundle_id, attack_history=attack_history
            )
        except ReviewBundleError as exc:
            raise SystemExit(f"could not build review bundle: {exc}") from exc
        copy_findings = check_bundle_copy(bundle)
        if copy_findings:
            raise SystemExit(
                f"obligation copy failed the appendix-A automated check: {copy_findings}"
            )
        written = write_review_bundle(bundle, args.out_dir)
        html_path = render_review_bundle_html(bundle, Path(args.out_dir) / "review.html")
        result: dict[str, Any] = {name: str(path) for name, path in written.items()}
        result["html"] = str(html_path)
        result["bundle_digest_sha256"] = bundle.bundle_digest_sha256
        _write_or_print(result, None)
        return

    if command == "submit":
        trace = load_trace(args.trace)
        if args.roster:
            roster_payload = json.loads(Path(args.roster).read_text(encoding="utf-8"))
            try:
                set_reviewer_roster(trace, ReviewerRoster.from_dict(roster_payload))
            except ReviewContractError as exc:
                raise SystemExit(f"could not install roster: {exc}") from exc
        record_payload = json.loads(Path(args.record).read_text(encoding="utf-8"))
        try:
            record = ReviewRecord.from_dict(record_payload)
        except ReviewContractError as exc:
            raise SystemExit(f"malformed review record: {exc}") from exc
        if record.reviewer_id != args.reviewer:
            raise SystemExit(
                f"--reviewer {args.reviewer!r} does not match the record's own "
                f"reviewer_id {record.reviewer_id!r}"
            )
        try:
            submit_review(trace, record)
        except (ReviewContractError, ReviewAuthorizationError) as exc:
            raise SystemExit(f"review submission rejected: {exc}") from exc
        result = {
            "submitted": True,
            "review_id": record.review_id,
            "decision": record.overall_decision.value,
        }
        if record.overall_decision is ReviewDecision.APPROVE:
            evidence_id = args.evidence_id or f"EV-REVIEW-{record.review_id}"
            evidence = review_to_evidence(
                trace,
                record.review_id,
                evidence_id=evidence_id,
                artifact_uri=f"review-record:{record.review_id}",
            )
            trace.add_evidence(evidence)
            result["evidence_id"] = evidence_id
        save_trace(trace, args.trace)
        _write_or_print(result, args.output)
        return

    if command == "revoke":
        trace = load_trace(args.trace)
        try:
            updated = revoke_review(trace, args.review_id, args.reason)
        except ReviewContractError as exc:
            raise SystemExit(str(exc)) from exc
        save_trace(trace, args.trace)
        _write_or_print(updated.to_dict(), args.output)
        return

    if command == "status":
        trace = load_trace(args.trace)
        payload = {
            "claim_id": args.claim,
            "nominations": [item.to_dict() for item in nominations_for_claim(trace, args.claim)],
            "reviews": [item.to_dict() for item in reviews_for_claim(trace, args.claim)],
        }
        _write_or_print(payload, args.output)
        return

    raise SystemExit(f"unknown review subcommand: {command}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="matharc-v02",
        description="MathArc Research v0.2 auditable theorem-research protocol",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="generate the deterministic failure-to-proof demo")
    demo.add_argument("--out-dir", default="artifacts/v02-demo")

    validate = sub.add_parser("validate", help="validate a v0.2 research trace")
    validate.add_argument("--trace", required=True)

    metrics = sub.add_parser("metrics", help="compute v0.2 research metrics")
    metrics.add_argument("--trace", required=True)
    metrics.add_argument("--output")

    plan = sub.add_parser("plan", help="select the next load-bearing research obligation")
    plan.add_argument("--trace", required=True)
    plan.add_argument("--failure-memory")
    plan.add_argument("--output")

    claude_status = sub.add_parser(
        "claude-status", help="report whether the Claude Code CLI worker bridge is available"
    )
    claude_status.add_argument("--executable")
    claude_status.add_argument("--output")

    run = sub.add_parser("run", help="run an autonomous multi-round research campaign")
    run.add_argument("--trace", required=True, help="path to an existing research trace")
    run.add_argument(
        "--role",
        action="append",
        default=None,
        help="worker role to run each round (repeatable); default: prover falsifier verifier",
    )
    run.add_argument("--rounds", type=int, default=DEFAULT_RUN_ROUNDS)
    run.add_argument("--max-rounds-without-gain", type=int, default=3)
    run.add_argument("--claude-executable")
    run.add_argument("--claude-model")
    run.add_argument(
        "--wall-seconds-budget",
        type=float,
        help=(
            "campaign wall-time budget in seconds; default is 1800 seconds. "
            "Use --no-budget only when an intentionally unbounded run is required"
        ),
    )
    run.add_argument("--cost-usd-budget", type=float)
    run.add_argument(
        "--no-budget",
        action="store_true",
        help="explicitly disable campaign budget limits; cannot be combined with budget flags",
    )
    run.add_argument("--persist", help="also persist the trace to this path after every round")
    run.add_argument("--output")

    review = sub.add_parser("review", help="expert review workflow (v0.3-review R0-R2)")
    review_sub = review.add_subparsers(dest="review_command", required=True)

    review_nominate = review_sub.add_parser(
        "nominate", help="R1 machine nomination pre-screen for one claim"
    )
    review_nominate.add_argument("--trace", required=True)
    review_nominate.add_argument("--claim", required=True)
    review_nominate.add_argument("--output")

    review_bundle_cmd = review_sub.add_parser(
        "bundle", help="build and write an R2 ReviewBundle for a claim"
    )
    review_bundle_cmd.add_argument("--trace", required=True)
    review_bundle_cmd.add_argument("--claim", required=True)
    review_bundle_cmd.add_argument("--bundle-id", required=True)
    review_bundle_cmd.add_argument("--out-dir", required=True)
    review_bundle_cmd.add_argument(
        "--attack-history",
        help="path to a JSON array of {attack_id, summary, emphasis} objects",
    )

    review_submit = review_sub.add_parser("submit", help="submit a ReviewRecord against a claim")
    review_submit.add_argument("--trace", required=True)
    review_submit.add_argument("--record", required=True, help="path to a ReviewRecord JSON payload")
    review_submit.add_argument(
        "--reviewer", required=True, help="must match the record's own reviewer_id"
    )
    review_submit.add_argument(
        "--roster", help="path to a ReviewerRoster JSON payload to install before submitting"
    )
    review_submit.add_argument(
        "--evidence-id", help="evidence_id to mint if the review is an APPROVE decision"
    )
    review_submit.add_argument("--output")

    review_revoke = review_sub.add_parser("revoke", help="revoke a previously submitted review")
    review_revoke.add_argument("--trace", required=True)
    review_revoke.add_argument("--review-id", required=True)
    review_revoke.add_argument("--reason", required=True)
    review_revoke.add_argument("--output")

    review_status = review_sub.add_parser(
        "status", help="show nominations and review records for one claim"
    )
    review_status.add_argument("--trace", required=True)
    review_status.add_argument("--claim", required=True)
    review_status.add_argument("--output")

    compare = sub.add_parser("compare", help="run a paired, qualification-gated benchmark comparison")
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--metric", action="append", required=True, help="NAME:maximize or NAME:minimize")
    compare.add_argument("--primary", action="append", required=True)
    compare.add_argument("--minimum-pairs", type=int, default=30)
    compare.add_argument("--bootstrap-samples", type=int, default=5000)
    compare.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "demo":
        paths = write_research_demo(args.out_dir)
        _write_or_print({key: str(value) for key, value in paths.items()}, None)
        return
    if args.command == "validate":
        validation = load_trace(args.trace).validate()
        _write_or_print(validation, None)
        raise SystemExit(0 if validation["valid"] else 1)
    if args.command == "metrics":
        _write_or_print(compute_research_metrics(load_trace(args.trace)), args.output)
        return
    if args.command == "plan":
        trace = load_trace(args.trace)
        memory = (
            FailureMemory.load(args.failure_memory)
            if args.failure_memory
            else FailureMemory()
        )
        orchestrator = ResearchOrchestrator(trace, memory)
        _write_or_print(orchestrator.plan_round().to_dict(), args.output)
        return
    if args.command == "claude-status":
        config = ClaudeCodeConfig.from_env()
        if args.executable:
            config.executable = args.executable
        _write_or_print(claude_code_status(config), args.output)
        return
    if args.command == "run":
        if args.rounds <= 0:
            raise SystemExit("--rounds must be positive")
        if args.max_rounds_without_gain <= 0:
            raise SystemExit("--max-rounds-without-gain must be positive")
        trace = load_trace(args.trace)
        roles = args.role or ["prover", "falsifier", "verifier"]
        claude_config = ClaudeCodeConfig.from_env()
        if args.claude_executable:
            claude_config.executable = args.claude_executable
        if args.claude_model:
            claude_config.model = args.claude_model
        runner = ClaudeCodeRunner(claude_config)
        workers = [LLMProposalWorker(role, runner=runner) for role in roles]
        budget = _build_run_budget(args)
        campaign = ResearchCampaign(
            trace,
            workers,
            budget=budget,
            max_rounds=args.rounds,
            max_rounds_without_gain=args.max_rounds_without_gain,
            persist_path=args.persist,
        )
        report = campaign.run()
        save_trace(trace, args.trace)
        _write_or_print(report.to_dict(), args.output)
        return
    if args.command == "review":
        _run_review_command(args)
        return

    directions: dict[str, str] = {}
    for specification in args.metric:
        try:
            name, direction = specification.rsplit(":", 1)
        except ValueError as exc:
            raise SystemExit(f"invalid --metric {specification!r}; use NAME:maximize") from exc
        if direction not in {"maximize", "minimize"}:
            raise SystemExit(f"invalid metric direction: {direction}")
        directions[name] = direction
    comparison = compare_agents(
        load_results(args.candidate),
        load_results(args.baseline),
        metric_directions=directions,
        primary_metrics=args.primary,
        minimum_pairs=args.minimum_pairs,
        bootstrap_samples=args.bootstrap_samples,
    )
    _write_or_print(comparison.to_dict(), args.output)
    raise SystemExit(0 if comparison.superiority_claim_allowed else 2)


if __name__ == "__main__":
    main()
