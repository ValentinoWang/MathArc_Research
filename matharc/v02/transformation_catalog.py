"""Strict, source-backed transformation operators for failed research routes.

The catalog supplies structured prompts for a planner; it does not prove that
any transformation is mathematically valid or guarantee that a useful route
will be found.  Entries are deliberately small and require a provenance
reference so an operator cannot enter the planner as an invented bulk list.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .schema import FailureClass, FailureRecord


class TransformationCatalogError(ValueError):
    """Raised when a transformation entry or linkage is not admissible."""


def _string_tuple(value: Any, *, field_name: str, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(value, str) or value is None:
        raise TransformationCatalogError(f"{field_name} must be an array of strings")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise TransformationCatalogError(
            f"{field_name} must be an array of strings"
        ) from exc
    result: list[str] = []
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise TransformationCatalogError(
                f"{field_name} must contain non-empty strings"
            )
        result.append(item.strip())
    if not allow_empty and not result:
        raise TransformationCatalogError(f"{field_name} must be non-empty")
    return tuple(result)


def _failure_class_tuple(value: Any) -> tuple[FailureClass, ...]:
    if isinstance(value, (str, bytes)) or value is None:
        raise TransformationCatalogError(
            "applicable_failure_classes must be an array of known FailureClass values"
        )
    try:
        values = tuple(value)
    except TypeError as exc:
        raise TransformationCatalogError(
            "applicable_failure_classes must be an array of known FailureClass values"
        ) from exc
    if not values:
        raise TransformationCatalogError("applicable_failure_classes must be non-empty")
    result: list[FailureClass] = []
    for value_item in values:
        try:
            failure_class = (
                value_item
                if isinstance(value_item, FailureClass)
                else FailureClass(str(value_item))
            )
        except (TypeError, ValueError) as exc:
            raise TransformationCatalogError(
                f"unknown failure class for transformation: {value_item!r}"
            ) from exc
        if failure_class not in result:
            result.append(failure_class)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class TransformationSpec:
    transformation_id: str
    applicable_failure_classes: tuple[FailureClass, ...]
    directive: Mapping[str, Any] | str
    structural_requirements: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.transformation_id, str) or not self.transformation_id.strip():
            raise TransformationCatalogError("transformation_id must be non-empty")
        object.__setattr__(self, "transformation_id", self.transformation_id.strip())
        object.__setattr__(
            self,
            "applicable_failure_classes",
            _failure_class_tuple(self.applicable_failure_classes),
        )
        if isinstance(self.directive, str):
            if not self.directive.strip():
                raise TransformationCatalogError("directive must be non-empty")
            object.__setattr__(self, "directive", self.directive.strip())
        elif isinstance(self.directive, Mapping):
            if not self.directive:
                raise TransformationCatalogError("directive must be non-empty")
            if any(not isinstance(key, str) or not key.strip() for key in self.directive):
                raise TransformationCatalogError("directive keys must be non-empty strings")
            object.__setattr__(self, "directive", MappingProxyType(dict(self.directive)))
        else:
            raise TransformationCatalogError("directive must be a string or object")
        object.__setattr__(
            self,
            "structural_requirements",
            _string_tuple(
                self.structural_requirements,
                field_name="structural_requirements",
            ),
        )
        provenance = self.provenance
        if isinstance(provenance, str):
            provenance = (provenance,)
        object.__setattr__(
            self,
            "provenance",
            _string_tuple(provenance, field_name="provenance", allow_empty=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "transformation_id": self.transformation_id,
            "applicable_failure_classes": [
                item.value for item in self.applicable_failure_classes
            ],
            "directive": (
                dict(self.directive)
                if isinstance(self.directive, Mapping)
                else self.directive
            ),
            "structural_requirements": list(self.structural_requirements),
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TransformationSpec":
        if not isinstance(payload, Mapping):
            raise TransformationCatalogError("transformation entry must be an object")
        allowed = {
            "transformation_id",
            "applicable_failure_classes",
            "directive",
            "structural_requirements",
            "provenance",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise TransformationCatalogError(
                f"unknown transformation fields: {sorted(unknown)}"
            )
        required = {"transformation_id", "applicable_failure_classes", "directive", "provenance"}
        missing = required - set(payload)
        if missing:
            raise TransformationCatalogError(
                f"transformation entry is missing fields: {sorted(missing)}"
            )
        return cls(
            transformation_id=payload["transformation_id"],
            applicable_failure_classes=payload["applicable_failure_classes"],
            directive=payload["directive"],
            structural_requirements=payload.get("structural_requirements", ()),
            provenance=payload["provenance"],
        )


Transformation = TransformationSpec
CatalogEntry = TransformationSpec
TransformationRecord = TransformationSpec
TransformationCatalogEntry = TransformationSpec


class TransformationCatalog:
    def __init__(self, entries: Iterable[TransformationSpec] = ()) -> None:
        normalized: list[TransformationSpec] = []
        seen: set[str] = set()
        for entry in entries:
            if isinstance(entry, Mapping):
                entry = TransformationSpec.from_dict(entry)
            if not isinstance(entry, TransformationSpec):
                raise TransformationCatalogError("catalog entries must be transformation objects")
            if entry.transformation_id in seen:
                raise TransformationCatalogError(
                    f"duplicate transformation_id: {entry.transformation_id}"
                )
            seen.add(entry.transformation_id)
            normalized.append(entry)
        self._entries = tuple(normalized)
        self._by_id = {entry.transformation_id: entry for entry in self._entries}

    def add(self, entry: TransformationSpec | Mapping[str, Any]) -> None:
        """Add one validated entry; bulk or implicit entries are never created."""

        candidate = entry if isinstance(entry, TransformationSpec) else TransformationSpec.from_dict(entry)
        if candidate.transformation_id in self._by_id:
            raise TransformationCatalogError(
                f"duplicate transformation_id: {candidate.transformation_id}"
            )
        self._entries = (*self._entries, candidate)
        self._by_id[candidate.transformation_id] = candidate

    register = add

    @property
    def entries(self) -> tuple[TransformationSpec, ...]:
        return self._entries

    def __iter__(self):
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, transformation_id: object) -> bool:
        return transformation_id in self._by_id

    def get(self, transformation_id: str) -> TransformationSpec:
        try:
            return self._by_id[transformation_id]
        except KeyError as exc:
            raise TransformationCatalogError(
                f"unknown transformation_id: {transformation_id}"
            ) from exc

    def applicable_to(self, failure: FailureRecord) -> tuple[TransformationSpec, ...]:
        if not isinstance(failure, FailureRecord):
            raise TransformationCatalogError(
                "transformation applicability requires a FailureRecord"
            )
        try:
            failure_class = (
                failure.failure_class
                if isinstance(failure.failure_class, FailureClass)
                else FailureClass(str(failure.failure_class))
            )
        except (TypeError, ValueError) as exc:
            raise TransformationCatalogError(
                f"unknown failure class on FailureRecord: {failure.failure_class!r}"
            ) from exc
        return tuple(
            entry
            for entry in self._entries
            if failure_class in entry.applicable_failure_classes
        )

    def directives_for(
        self,
        failure: FailureRecord,
        *,
        failed_mechanism_signature: Iterable[str] = (),
    ) -> tuple[dict[str, Any], ...]:
        if not isinstance(failure.failure_class, FailureClass):
            raise TransformationCatalogError(
                f"unknown failure class on FailureRecord: {failure.failure_class!r}"
            )
        return tuple(
            {
                "failure_id": failure.failure_id,
                "failure_class": failure.failure_class.value,
                "failed_route_id": failure.route_id,
                "transformation_id": entry.transformation_id,
                "directive": (
                    dict(entry.directive)
                    if isinstance(entry.directive, Mapping)
                    else entry.directive
                ),
                "structural_requirements": list(entry.structural_requirements),
                "provenance": list(entry.provenance),
                "failed_mechanism_signature": list(failed_mechanism_signature),
            }
            for entry in self.applicable_to(failure)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"transformations": [entry.to_dict() for entry in self._entries]}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TransformationCatalog":
        if not isinstance(payload, Mapping):
            raise TransformationCatalogError("transformation catalog must be an object")
        unknown = set(payload) - {"transformations"}
        if unknown:
            raise TransformationCatalogError(
                f"unknown transformation catalog fields: {sorted(unknown)}"
            )
        raw_entries = payload.get("transformations")
        if isinstance(raw_entries, (str, bytes)) or raw_entries is None:
            raise TransformationCatalogError("transformations must be an array")
        try:
            entries = tuple(raw_entries)
        except TypeError as exc:
            raise TransformationCatalogError("transformations must be an array") from exc
        return cls(TransformationSpec.from_dict(entry) for entry in entries)

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        for entry in self._entries:
            if not entry.provenance:
                errors.append(f"transformation {entry.transformation_id} has no provenance")
        return {
            "valid": not errors,
            "errors": errors,
            "count": len(self._entries),
            "transformation_ids": [entry.transformation_id for entry in self._entries],
        }


def default_transformation_catalog() -> TransformationCatalog:
    """Return the small source-backed catalog used by the default planner."""

    return TransformationCatalog(
        (
            TransformationSpec(
                transformation_id="narrow_scope_after_overreach",
                applicable_failure_classes=(FailureClass.SCOPE_OVERREACH,),
                directive={
                    "action": "narrow_scope",
                    "instruction": "state the smallest domain supported by the witness",
                },
                structural_requirements=(
                    "state the removed scope explicitly",
                    "add a boundary-case kill test",
                ),
                provenance=("docs/DISCOVERY_PLANE_V04.md#x1",),
            ),
            TransformationSpec(
                transformation_id="independent_reconstruction_after_common_mode",
                applicable_failure_classes=(FailureClass.NON_INDEPENDENT_CHECKER,),
                directive={
                    "action": "change_verification_formalism",
                    "instruction": "reconstruct the result with an independent checker",
                },
                structural_requirements=(
                    "use a distinct implementation or proof formalism",
                    "record the independence group",
                ),
                provenance=("matharc/v02/trace.py:525-542",),
            ),
            TransformationSpec(
                transformation_id="new_mechanism_after_route_duplication",
                applicable_failure_classes=(FailureClass.ROUTE_DUPLICATION,),
                directive={
                    "action": "change_mechanism",
                    "instruction": "open a route with a genuinely different mechanism",
                },
                structural_requirements=(
                    "preserve a cheap falsification test",
                    "explain the mechanism difference",
                ),
                provenance=("matharc/v02/trace.py:113-121",),
            ),
        )
    )


DEFAULT_TRANSFORMATION_CATALOG = default_transformation_catalog()
