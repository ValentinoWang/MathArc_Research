from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.local_store import LocalStoreError
from matharc.v02.topic_portfolio import CriterionVerdict, TOPIC_CRITERIA, TopicCandidate, TopicCriterion, TopicPortfolio, TopicPortfolioStore, TopicState
from matharc.v02.workspace_bundle import write_full_workspace_bundle


def criteria() -> tuple[TopicCriterion, ...]:
    return tuple(TopicCriterion(key, CriterionVerdict.DECLARED, (f"EV-{index}",), "manual evidence declaration") for index, key in enumerate(TOPIC_CRITERIA, 1))


class TopicPortfolioTests(unittest.TestCase):
    def test_round_trip_and_deterministic_seats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            topic = TopicCandidate("union-closed", "Union-closed", TopicState.ACTIVE, 1, criteria(), ("OBS-1",))
            portfolio = TopicPortfolio("P-1", 1, (topic,))
            store = TopicPortfolioStore(Path(directory) / "portfolio")
            self.assertEqual(store.create(portfolio).digest_sha256, store.load().digest_sha256)
            self.assertEqual(store.create(portfolio), portfolio)

    def test_rejects_noncanonical_and_tampered_records(self) -> None:
        with self.assertRaises(LocalStoreError):
            TopicCandidate("a", "A", TopicState.CANDIDATE, None, tuple(reversed(criteria())), ())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "portfolio"; store = TopicPortfolioStore(root)
            topic = TopicCandidate("a", "A", TopicState.ACTIVE, 1, criteria(), ())
            store.create(TopicPortfolio("P", 1, (topic,)))
            data = json.loads((root / "topic-portfolio.json").read_text(encoding="utf-8")); data["portfolio"]["candidates"][0]["name"] = "tampered"
            (root / "topic-portfolio.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(LocalStoreError): store.load()

    def test_rejects_workspace_location_and_slot_collision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = TopicCandidate("a", "A", TopicState.ACTIVE, 1, criteria(), ())
            second = TopicCandidate("b", "B", TopicState.ACTIVE, 1, criteria(), ())
            with self.assertRaises(LocalStoreError): TopicPortfolio("P", 2, (first, second))
            workspace = Path(directory) / "workspace"; write_full_workspace_bundle(workspace)
            with self.assertRaises(LocalStoreError): TopicPortfolioStore(workspace / "portfolio")


if __name__ == "__main__": unittest.main()
