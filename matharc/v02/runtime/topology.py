"""Compile an explicit, isolated topology for research members.

The topology is intentionally runtime-local.  It carries enough information
for a scheduler to enforce budgets and write isolation without granting a
worker authority over the shared research state.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


class TopologyValidationError(ValueError):
    """Raised when a route/member declaration is incomplete or unsafe."""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TopologyValidationError(f"member {field_name} is required")
    return value.strip()


def _number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise TopologyValidationError(f"member {field_name} must be a non-negative number")
    return float(value)


@dataclass(frozen=True, slots=True)
class ResearchMember:
    member_id: str
    role: str
    mechanism: str
    budget: Mapping[str, float]
    objective: str
    write_scope: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_id", _required_text(self.member_id, "member_id"))
        object.__setattr__(self, "role", _required_text(self.role, "role"))
        object.__setattr__(self, "mechanism", _required_text(self.mechanism, "mechanism"))
        object.__setattr__(self, "objective", _required_text(self.objective, "objective"))
        if not isinstance(self.budget, Mapping) or not self.budget:
            raise TopologyValidationError("member budget is required")
        budget = {str(k): _number(v, f"budget.{k}") for k, v in self.budget.items()}
        object.__setattr__(self, "budget", MappingProxyType(budget))
        raw_scopes = self.write_scope
        scopes = tuple(
            _required_text(item.get("path") if isinstance(item, Mapping) else item, "write_scope")
            for item in raw_scopes
        )
        if not scopes:
            raise TopologyValidationError("member write_scope is required")
        if len(set(scopes)) != len(scopes):
            raise TopologyValidationError("member write_scope contains duplicates")
        object.__setattr__(self, "write_scope", scopes)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResearchMember":
        if not isinstance(value, Mapping):
            raise TopologyValidationError("research member must be an object")
        # Accept mechanism_id as a readable alias used by route declarations.
        mechanism = value.get("mechanism", value.get("mechanism_id"))
        return cls(
            member_id=value.get("member_id", value.get("id")),
            role=value.get("role", value.get("role_id")),
            mechanism=mechanism or value.get("strategy"),
            budget=value.get("budget"),
            objective=value.get("objective", value.get("goal")),
            write_scope=tuple(value.get("write_scope", value.get("write_targets", ()))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "role": self.role,
            "mechanism": self.mechanism,
            "budget": dict(self.budget),
            "objective": self.objective,
            "write_scope": list(self.write_scope),
        }


@dataclass(frozen=True, slots=True)
class ResearchTopology:
    route_id: str
    members: tuple[ResearchMember, ...]
    dependencies: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    max_concurrency: int = 1
    topology_digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", _required_text(self.route_id, "route_id"))
        if not self.members:
            raise TopologyValidationError("at least one research member is required")
        ids = [m.member_id for m in self.members]
        if len(set(ids)) != len(ids):
            raise TopologyValidationError("member_id values must be unique")
        if isinstance(self.max_concurrency, bool) or not isinstance(self.max_concurrency, int) or self.max_concurrency < 1:
            raise TopologyValidationError("max_concurrency must be a positive integer")
        if self.max_concurrency > len(self.members):
            object.__setattr__(self, "max_concurrency", len(self.members))
        deps = {str(k): tuple(str(x) for x in v) for k, v in dict(self.dependencies).items()}
        unknown = set(deps) - set(ids) | {d for values in deps.values() for d in values} - set(ids)
        if unknown:
            raise TopologyValidationError(f"dependencies reference unknown members: {sorted(unknown)}")
        object.__setattr__(self, "dependencies", MappingProxyType(deps))
        scopes: dict[str, str] = {}
        for member in self.members:
            for path in member.write_scope:
                if path in scopes:
                    raise TopologyValidationError(f"write_scope overlaps between {scopes[path]} and {member.member_id}: {path}")
                scopes[path] = member.member_id
        canonical = {"route_id": self.route_id, "members": [m.to_dict() for m in self.members], "dependencies": deps, "max_concurrency": self.max_concurrency}
        object.__setattr__(self, "topology_digest_sha256", hashlib.sha256(_json(canonical).encode()).hexdigest())

    def to_dict(self) -> dict[str, Any]:
        return {"route_id": self.route_id, "members": [m.to_dict() for m in self.members], "dependencies": {k: list(v) for k, v in self.dependencies.items()}, "max_concurrency": self.max_concurrency, "topology_digest_sha256": self.topology_digest_sha256}


def compile_topology(route: str | Mapping[str, Any], members: Iterable[ResearchMember | Mapping[str, Any]] | None = None, *, max_concurrency: int | None = None) -> ResearchTopology:
    """Compile a route and members, rejecting missing or conflicting declarations."""
    if isinstance(route, Mapping):
        route_id = route.get("route_id", route.get("id", route.get("route")))
        if members is None:
            members = route.get("members", route.get("roles"))
        dependencies = route.get("dependencies", route.get("depends_on", {}))
        if max_concurrency is None:
            max_concurrency = route.get("max_concurrency", route.get("concurrency", 1))
    else:
        route_id, dependencies = route, {}
    if members is None:
        raise TopologyValidationError("research members are required")
    parsed = tuple(item if isinstance(item, ResearchMember) else ResearchMember.from_mapping(item) for item in members)
    return ResearchTopology(route_id=route_id, members=parsed, dependencies=dependencies, max_concurrency=max_concurrency or 1)


compile_research_topology = compile_topology
build_topology = compile_topology
ResearchTopologyCompiler = compile_topology

__all__ = ["ResearchMember", "ResearchTopology", "TopologyValidationError", "compile_topology", "compile_research_topology", "build_topology"]
