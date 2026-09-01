"""Manual-evidence candidate-problem gates with no research-status inference."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .local_store import LocalStoreError, exclusive_lock, external_root, read_json, state_digest, strict_mapping, write_json_atomic
from .schema import digest_json


GATE_IDS = (
    "source_version_pinned", "statement_version_frozen", "reported_status_evidence", "frontier_gap_reconstructed", "importance_evidence", "auditable_acceptance", "strongest_baseline_reproduced", "fallback_output_declared", "expert_review_channel",
)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise LocalStoreError(f"{label} must be non-empty text")
    return value


class GateVerdict(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True)
class GateEvidence:
    gate_id: str
    verdict: GateVerdict
    evidence_ref: str
    reviewed_at: str

    def __post_init__(self) -> None:
        if self.gate_id not in GATE_IDS: raise LocalStoreError("unsupported candidate-problem gate")
        if not isinstance(self.verdict, GateVerdict): raise LocalStoreError("unsupported gate verdict")
        _text(self.evidence_ref, "gate evidence reference"); _text(self.reviewed_at, "gate reviewed_at")

    def to_dict(self) -> dict[str, str]: return {"gate_id": self.gate_id, "verdict": self.verdict.value, "evidence_ref": self.evidence_ref, "reviewed_at": self.reviewed_at}

    @classmethod
    def from_dict(cls, value: object) -> "GateEvidence":
        data = strict_mapping(value, {"gate_id", "verdict", "evidence_ref", "reviewed_at"}, "gate evidence")
        return cls(_text(data["gate_id"], "gate_id"), GateVerdict(data["verdict"]), _text(data["evidence_ref"], "evidence_ref"), _text(data["reviewed_at"], "reviewed_at"))


@dataclass(frozen=True, slots=True)
class ProblemStatementVersion:
    problem_id: str
    version: int
    statement: str

    def __post_init__(self) -> None:
        _text(self.problem_id, "problem_id"); _text(self.statement, "statement")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1: raise LocalStoreError("statement version must be positive")

    @property
    def statement_version_id(self) -> str: return f"{self.problem_id}@{self.version}"
    @property
    def digest_sha256(self) -> str: return digest_json({"problem_id": self.problem_id, "version": self.version, "statement": self.statement})
    def to_dict(self) -> dict[str, Any]: return {"problem_id": self.problem_id, "version": self.version, "statement": self.statement, "digest_sha256": self.digest_sha256}
    @classmethod
    def from_dict(cls, value: object) -> "ProblemStatementVersion":
        data = strict_mapping(value, {"problem_id", "version", "statement", "digest_sha256"}, "problem statement version")
        result = cls(_text(data["problem_id"], "problem_id"), data["version"], _text(data["statement"], "statement"))
        if data["digest_sha256"] != result.digest_sha256: raise LocalStoreError("problem statement digest mismatch")
        return result


@dataclass(frozen=True, slots=True)
class CandidateProblem:
    problem_id: str
    statement_version_id: str
    gates: tuple[GateEvidence, ...]

    def __post_init__(self) -> None:
        _text(self.problem_id, "problem_id"); _text(self.statement_version_id, "statement_version_id")
        if tuple(item.gate_id for item in self.gates) != GATE_IDS: raise LocalStoreError("candidate problem must contain exactly the nine fixed gates")
    @property
    def ready_to_start(self) -> bool: return all(item.verdict is GateVerdict.PASSED for item in self.gates)
    def to_dict(self) -> dict[str, Any]: return {"problem_id": self.problem_id, "statement_version_id": self.statement_version_id, "gates": [item.to_dict() for item in self.gates], "ready_to_start": self.ready_to_start}
    @classmethod
    def from_dict(cls, value: object) -> "CandidateProblem":
        data = strict_mapping(value, {"problem_id", "statement_version_id", "gates", "ready_to_start"}, "candidate problem")
        if not isinstance(data["gates"], list): raise LocalStoreError("candidate gates must be an array")
        result = cls(_text(data["problem_id"], "problem_id"), _text(data["statement_version_id"], "statement version id"), tuple(GateEvidence.from_dict(item) for item in data["gates"]))
        if data["ready_to_start"] is not result.ready_to_start: raise LocalStoreError("candidate ready flag is stale")
        return result


class ResultRelation(str, Enum):
    DERIVES_FROM = "DERIVES_FROM"
    BOUNDED_BY = "BOUNDED_BY"
    BLOCKED_BY = "BLOCKED_BY"
    COVERS = "COVERS"


@dataclass(frozen=True, slots=True)
class ResultGraphEdge:
    edge_id: str
    source_version_id: str
    target_version_id: str
    relation: ResultRelation
    evidence_ref: str

    def __post_init__(self) -> None:
        _text(self.edge_id, "edge_id"); _text(self.source_version_id, "source version id"); _text(self.target_version_id, "target version id"); _text(self.evidence_ref, "edge evidence reference")
        if self.source_version_id == self.target_version_id: raise LocalStoreError("result graph self edges are forbidden")
        if not isinstance(self.relation, ResultRelation): raise LocalStoreError("unsupported result graph relation")
    def to_dict(self) -> dict[str, str]: return {"edge_id": self.edge_id, "source_version_id": self.source_version_id, "target_version_id": self.target_version_id, "relation": self.relation.value, "evidence_ref": self.evidence_ref}
    @classmethod
    def from_dict(cls, value: object) -> "ResultGraphEdge":
        data = strict_mapping(value, {"edge_id", "source_version_id", "target_version_id", "relation", "evidence_ref"}, "result graph edge")
        return cls(_text(data["edge_id"], "edge_id"), _text(data["source_version_id"], "source version id"), _text(data["target_version_id"], "target version id"), ResultRelation(data["relation"]), _text(data["evidence_ref"], "evidence ref"))


@dataclass(frozen=True, slots=True)
class ResultGraph:
    nodes: tuple[str, ...]
    edges: tuple[ResultGraphEdge, ...]
    def __post_init__(self) -> None:
        if self.nodes != tuple(sorted(self.nodes)) or not self.nodes or any(not item.strip() for item in self.nodes): raise LocalStoreError("result graph nodes must be sorted non-empty ids")
        if len(set(self.nodes)) != len(self.nodes) or tuple(item.edge_id for item in self.edges) != tuple(sorted(item.edge_id for item in self.edges)) or len({item.edge_id for item in self.edges}) != len(self.edges): raise LocalStoreError("result graph identities are invalid")
        if any(item.source_version_id not in self.nodes or item.target_version_id not in self.nodes for item in self.edges): raise LocalStoreError("result graph edge has an unknown node")
        adjacency: dict[str, list[str]] = {item: [] for item in self.nodes}
        for edge in self.edges: adjacency[edge.source_version_id].append(edge.target_version_id)
        visiting: set[str] = set(); visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting: raise LocalStoreError("result graph must be acyclic")
            if node not in visited:
                visiting.add(node)
                for target in adjacency[node]: visit(target)
                visiting.remove(node); visited.add(node)
        for node in self.nodes: visit(node)
    def to_dict(self) -> dict[str, Any]: return {"nodes": list(self.nodes), "edges": [item.to_dict() for item in self.edges]}
    @classmethod
    def from_dict(cls, value: object) -> "ResultGraph":
        data = strict_mapping(value, {"nodes", "edges"}, "result graph")
        if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list): raise LocalStoreError("result graph arrays are invalid")
        return cls(tuple(_text(item, "result graph node") for item in data["nodes"]), tuple(ResultGraphEdge.from_dict(item) for item in data["edges"]))


class ProblemGateStore:
    _FILENAME = "candidate-problems.json"
    def __init__(self, root: str) -> None: self.root = external_root(root); self.path = self.root / self._FILENAME
    def replace(self, statements: tuple[ProblemStatementVersion, ...], candidates: tuple[CandidateProblem, ...], graph: ResultGraph) -> None:
        if tuple(item.statement_version_id for item in statements) != tuple(sorted(item.statement_version_id for item in statements)) or len({item.statement_version_id for item in statements}) != len(statements): raise LocalStoreError("statements must be unique and ordered")
        ids = {item.statement_version_id for item in statements}
        if tuple(item.problem_id for item in candidates) != tuple(sorted(item.problem_id for item in candidates)) or len({item.problem_id for item in candidates}) != len(candidates): raise LocalStoreError("candidates must be unique and ordered")
        if any(item.statement_version_id not in ids for item in candidates) or set(graph.nodes) != ids: raise LocalStoreError("problem records must reference known statement versions")
        with exclusive_lock(self.root, self._FILENAME):
            payload: dict[str, Any] = {"schema_version": "1.0", "statements": [item.to_dict() for item in statements], "candidates": [item.to_dict() for item in candidates], "graph": graph.to_dict()}
            payload["state_digest_sha256"] = state_digest(payload); write_json_atomic(self.path, payload)
    def load(self) -> tuple[tuple[ProblemStatementVersion, ...], tuple[CandidateProblem, ...], ResultGraph]:
        data = strict_mapping(read_json(self.path, "candidate problem store"), {"schema_version", "statements", "candidates", "graph", "state_digest_sha256"}, "candidate problem store")
        if data["schema_version"] != "1.0" or data["state_digest_sha256"] != state_digest(data) or not isinstance(data["statements"], list) or not isinstance(data["candidates"], list): raise LocalStoreError("candidate problem state integrity check failed")
        statements = tuple(ProblemStatementVersion.from_dict(item) for item in data["statements"]); candidates = tuple(CandidateProblem.from_dict(item) for item in data["candidates"]); graph = ResultGraph.from_dict(data["graph"])
        self._validate(statements, candidates, graph); return statements, candidates, graph
    @staticmethod
    def _validate(statements: tuple[ProblemStatementVersion, ...], candidates: tuple[CandidateProblem, ...], graph: ResultGraph) -> None:
        if tuple(item.statement_version_id for item in statements) != tuple(sorted(item.statement_version_id for item in statements)) or tuple(item.problem_id for item in candidates) != tuple(sorted(item.problem_id for item in candidates)) or set(graph.nodes) != {item.statement_version_id for item in statements}: raise LocalStoreError("candidate problem state ordering or references are invalid")
