"""Read-only console projections for existing source and topic observations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .local_store import external_root
from .source_registry import SourceRegistry
from .topic_observation import TopicObservationRunner


@dataclass(frozen=True, slots=True)
class TopicStoreConfig:
    """An explicit, pre-existing store that the console may read."""

    root: Path
    topic_id: str
    initial_cursor: str

    def open_read_only(self) -> TopicObservationRunner:
        root = external_root(self.root)
        required = (
            root,
            root / "topic-observation-state.json",
            root / "literature",
            root / "literature" / "observations.json",
            root / "literature" / "artifacts" / "manifest.json",
        )
        if not all(path.is_dir() if path == root or path.name == "literature" else path.is_file() for path in required):
            raise ValueError("topic store must already contain complete observation state")
        # TopicObservationRunner performs the existing schema validation when
        # its properties are read.  All directories above are required first,
        # so this construction cannot bootstrap a store as a side effect.
        return TopicObservationRunner(
            root,
            topic_id=self.topic_id,
            initial_cursor=self.initial_cursor,
        )


def console_topic_projection(
    registry: SourceRegistry,
    *,
    topic_store: TopicObservationRunner | None = None,
) -> dict[str, Any]:
    """Project durable observation facts without inferring research status."""

    claims = [
        {
            "source_claim_id": item.source_claim_id,
            "status": item.status.value,
            "canonical_uri": item.canonical_uri,
            "pinned_version": item.pinned_version,
            "locator": item.locator,
            "source_digest_sha256": item.source_digest_sha256,
            "verification_method": item.verification_method,
            "statement_correspondence": item.statement_correspondence,
            "limitations": list(item.limitations),
        }
        for item in registry.claims
    ]
    observations: list[dict[str, Any]] = []
    manual_queue: list[dict[str, Any]] = []
    next_cursor: str | None = None
    if topic_store is not None:
        observations = [item.to_dict() for item in topic_store.literature.observations]
        manual_queue = [item.to_dict() for item in topic_store.manual_queue]
        next_cursor = topic_store.next_cursor
    counts = Counter(item.get("status", "UNKNOWN") for item in observations)
    observed = counts.get("OBSERVED", 0)
    return {
        "schema_version": "1.0",
        "source_claims": claims,
        "topic_observations": {
            "available": topic_store is not None,
            "counts_by_status": dict(sorted(counts.items())),
            "observed_count": observed,
            "pending_count": counts.get("PENDING", 0),
            "manual_review_count": len(topic_store.manual_queue) if topic_store is not None else 0,
            "manual_review_queue": manual_queue,
            "next_cursor": next_cursor,
            "external_search_statistics": (
                "not_inferred" if observed == 0 else "durable_observations_only"
            ),
        },
        "status_boundary": (
            "This projection does not infer open, resolved, novelty, or new-result status."
        ),
    }
