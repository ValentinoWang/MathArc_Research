"""Read-only console projections for existing source and topic observations."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from .source_registry import SourceRegistry
from .topic_observation import TopicObservationRunner


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
    if topic_store is not None:
        observations = [item.to_dict() for item in topic_store.literature.observations]
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
            "external_search_statistics": (
                "not_inferred" if observed == 0 else "durable_observations_only"
            ),
        },
        "status_boundary": (
            "This projection does not infer open, resolved, novelty, or new-result status."
        ),
    }
