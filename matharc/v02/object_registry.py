from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import digest_json, utc_now


class ObjectStatus(str, Enum):
    PROPOSED = "PROPOSED"
    DEFINED = "DEFINED"
    VERIFIED = "VERIFIED"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


class ObjectKind(str, Enum):
    SET = "SET"
    SPACE = "SPACE"
    ALGEBRA = "ALGEBRA"
    GROUP = "GROUP"
    CATEGORY = "CATEGORY"
    FUNCTOR = "FUNCTOR"
    MAP = "MAP"
    OPERATOR = "OPERATOR"
    MEASURE = "MEASURE"
    DISTRIBUTION = "DISTRIBUTION"
    RANDOM_VARIABLE = "RANDOM_VARIABLE"
    EQUATION = "EQUATION"
    INVARIANT = "INVARIANT"
    CERTIFICATE = "CERTIFICATE"
    PARAMETER = "PARAMETER"
    OTHER = "OTHER"


@dataclass(slots=True)
class MathematicalObject:
    object_id: str
    symbol: str
    name: str
    kind: ObjectKind
    definition: str
    type_signature: str
    construction_source: str
    current_role: str
    status: ObjectStatus = ObjectStatus.PROPOSED
    domain: str = ""
    codomain: str = ""
    topology_or_regularities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    applicability_boundary: str = ""
    failure_if_removed: str = ""
    revision: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "symbol": self.symbol,
            "name": self.name,
            "kind": self.kind.value,
            "definition": self.definition,
            "type_signature": self.type_signature,
            "construction_source": self.construction_source,
            "current_role": self.current_role,
            "status": self.status.value,
            "domain": self.domain,
            "codomain": self.codomain,
            "topology_or_regularities": list(self.topology_or_regularities),
            "dependencies": list(self.dependencies),
            "assumptions": list(self.assumptions),
            "source_refs": list(self.source_refs),
            "applicability_boundary": self.applicability_boundary,
            "failure_if_removed": self.failure_if_removed,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MathematicalObject":
        allowed = {
            "object_id",
            "symbol",
            "name",
            "kind",
            "definition",
            "type_signature",
            "construction_source",
            "current_role",
            "status",
            "domain",
            "codomain",
            "topology_or_regularities",
            "dependencies",
            "assumptions",
            "source_refs",
            "applicability_boundary",
            "failure_if_removed",
            "revision",
            "created_at",
            "updated_at",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown mathematical-object fields: {sorted(unknown)}")
        return cls(
            object_id=str(payload["object_id"]),
            symbol=str(payload["symbol"]),
            name=str(payload["name"]),
            kind=ObjectKind(str(payload["kind"])),
            definition=str(payload["definition"]),
            type_signature=str(payload["type_signature"]),
            construction_source=str(payload["construction_source"]),
            current_role=str(payload["current_role"]),
            status=ObjectStatus(str(payload.get("status", ObjectStatus.PROPOSED.value))),
            domain=str(payload.get("domain", "")),
            codomain=str(payload.get("codomain", "")),
            topology_or_regularities=tuple(
                str(item) for item in payload.get("topology_or_regularities", [])
            ),
            dependencies=tuple(str(item) for item in payload.get("dependencies", [])),
            assumptions=tuple(str(item) for item in payload.get("assumptions", [])),
            source_refs=tuple(str(item) for item in payload.get("source_refs", [])),
            applicability_boundary=str(payload.get("applicability_boundary", "")),
            failure_if_removed=str(payload.get("failure_if_removed", "")),
            revision=int(payload.get("revision", 0)),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
        )


class ObjectRegistry:
    """Stable registry for mathematical objects used by a research run.

    The registry enforces the user's rigorous-object protocol: each important
    object has a stable symbol, explicit definition, type, source, role, state,
    and applicability boundary before it can be marked VERIFIED.
    """

    def __init__(self, objects: Iterable[MathematicalObject] = ()) -> None:
        self._objects: dict[str, MathematicalObject] = {}
        for item in objects:
            self.add(item)

    @property
    def objects(self) -> tuple[MathematicalObject, ...]:
        return tuple(self._objects[key] for key in sorted(self._objects))

    def get(self, object_id: str) -> MathematicalObject:
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise KeyError(f"unknown mathematical object: {object_id}") from exc

    def add(self, item: MathematicalObject) -> None:
        if item.object_id in self._objects:
            raise ValueError(f"duplicate mathematical-object id: {item.object_id}")
        if any(existing.symbol == item.symbol for existing in self._objects.values()):
            raise ValueError(f"duplicate mathematical symbol: {item.symbol}")
        missing = [dependency for dependency in item.dependencies if dependency not in self._objects]
        if missing:
            raise ValueError(
                f"object {item.object_id} has undeclared dependencies: {missing}"
            )
        self._objects[item.object_id] = item
        cycle = self._find_cycle()
        if cycle:
            del self._objects[item.object_id]
            raise ValueError(f"object dependency cycle: {' -> '.join(cycle)}")

    def revise(
        self,
        object_id: str,
        *,
        definition: str | None = None,
        type_signature: str | None = None,
        current_role: str | None = None,
        applicability_boundary: str | None = None,
    ) -> MathematicalObject:
        item = self.get(object_id)
        if item.status is ObjectStatus.VERIFIED:
            raise ValueError(
                "verified objects are immutable; deprecate and create a new object revision"
            )
        if definition is not None:
            item.definition = definition
        if type_signature is not None:
            item.type_signature = type_signature
        if current_role is not None:
            item.current_role = current_role
        if applicability_boundary is not None:
            item.applicability_boundary = applicability_boundary
        item.revision += 1
        item.updated_at = utc_now()
        return item

    def verify(self, object_id: str) -> MathematicalObject:
        item = self.get(object_id)
        issues = self.object_issues(item)
        if issues:
            raise ValueError("; ".join(issues))
        if any(
            self.get(dependency).status is not ObjectStatus.VERIFIED
            for dependency in item.dependencies
        ):
            unresolved = [
                dependency
                for dependency in item.dependencies
                if self.get(dependency).status is not ObjectStatus.VERIFIED
            ]
            raise ValueError(
                f"object {object_id} has unverified dependencies: {unresolved}"
            )
        item.status = ObjectStatus.VERIFIED
        item.updated_at = utc_now()
        return item

    def deprecate(self, object_id: str) -> None:
        item = self.get(object_id)
        item.status = ObjectStatus.DEPRECATED
        item.updated_at = utc_now()
        for candidate in self._objects.values():
            if object_id in candidate.dependencies and candidate.status is ObjectStatus.VERIFIED:
                candidate.status = ObjectStatus.DEFINED
                candidate.updated_at = utc_now()

    def object_issues(self, item: MathematicalObject) -> list[str]:
        issues: list[str] = []
        required = {
            "symbol": item.symbol,
            "name": item.name,
            "definition": item.definition,
            "type_signature": item.type_signature,
            "construction_source": item.construction_source,
            "current_role": item.current_role,
            "applicability_boundary": item.applicability_boundary,
            "failure_if_removed": item.failure_if_removed,
        }
        for field_name, value in required.items():
            if not value.strip():
                issues.append(f"object {item.object_id} lacks {field_name}")
        if item.kind in {ObjectKind.MAP, ObjectKind.OPERATOR, ObjectKind.FUNCTOR}:
            if not item.domain.strip():
                issues.append(f"typed arrow {item.object_id} lacks a domain")
            if not item.codomain.strip():
                issues.append(f"typed arrow {item.object_id} lacks a codomain")
        for dependency in item.dependencies:
            if dependency not in self._objects:
                issues.append(f"object {item.object_id} has missing dependency {dependency}")
        return issues

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        symbols: dict[str, str] = {}
        for item in self._objects.values():
            if item.symbol in symbols:
                errors.append(
                    f"symbol {item.symbol} is shared by {symbols[item.symbol]} and {item.object_id}"
                )
            symbols[item.symbol] = item.object_id
            issues = self.object_issues(item)
            if item.status is ObjectStatus.VERIFIED:
                errors.extend(issues)
            else:
                warnings.extend(issues)
            if item.status is ObjectStatus.VERIFIED:
                unresolved = [
                    dependency
                    for dependency in item.dependencies
                    if self._objects.get(dependency) is None
                    or self._objects[dependency].status is not ObjectStatus.VERIFIED
                ]
                if unresolved:
                    errors.append(
                        f"verified object {item.object_id} has unverified dependencies {unresolved}"
                    )
        cycle = self._find_cycle()
        if cycle:
            errors.append(f"object dependency cycle: {' -> '.join(cycle)}")
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "object_count": len(self._objects),
            "verified_count": sum(
                item.status is ObjectStatus.VERIFIED for item in self._objects.values()
            ),
            "registry_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "objects": [item.to_dict() for item in self.objects],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObjectRegistry":
        if set(payload) - {"schema_version", "objects"}:
            raise ValueError("unknown object-registry fields")
        if str(payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported object-registry schema")
        registry = cls()
        pending = [MathematicalObject.from_dict(item) for item in payload.get("objects", [])]
        while pending:
            progress = False
            for item in pending[:]:
                if all(dependency in registry._objects for dependency in item.dependencies):
                    registry.add(item)
                    pending.remove(item)
                    progress = True
            if not progress:
                unresolved = {item.object_id: list(item.dependencies) for item in pending}
                raise ValueError(f"unresolvable object dependencies: {unresolved}")
        return registry

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    @classmethod
    def load(cls, path: str | Path) -> "ObjectRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("object-registry root must be an object")
        return cls.from_dict(payload)

    def _find_cycle(self) -> tuple[str, ...]:
        state: dict[str, int] = {}
        stack: list[str] = []

        def visit(object_id: str) -> tuple[str, ...]:
            state[object_id] = 1
            stack.append(object_id)
            for dependency in self._objects[object_id].dependencies:
                if dependency not in self._objects:
                    continue
                if state.get(dependency, 0) == 0:
                    cycle = visit(dependency)
                    if cycle:
                        return cycle
                elif state.get(dependency) == 1:
                    index = stack.index(dependency)
                    return tuple((*stack[index:], dependency))
            stack.pop()
            state[object_id] = 2
            return ()

        for object_id in sorted(self._objects):
            if state.get(object_id, 0) == 0:
                cycle = visit(object_id)
                if cycle:
                    return cycle
        return ()
