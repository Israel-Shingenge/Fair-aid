"""Translate between the Django world (models, serializer data) and the engine's plain types."""
from typing import Optional, Sequence, Tuple

from apps.schemes.models import BursaryScheme

from .engine import SchemeCriteria, StudentProfile


def _as_tuple(values: Optional[Sequence[str]]) -> Optional[Tuple[str, ...]]:
    return tuple(values) if values else None


def scheme_to_criteria(scheme: BursaryScheme) -> SchemeCriteria:
    return SchemeCriteria(
        name=scheme.name,
        description=scheme.description or "",
        min_nqf_level=scheme.min_nqf_level,
        max_household_income=scheme.max_household_income,
        requires_disability=scheme.requires_disability,
        eligible_fields_of_study=_as_tuple(scheme.eligible_fields_of_study),
        eligible_regions=_as_tuple(scheme.eligible_regions),
    )


def profile_from_validated(data: dict) -> StudentProfile:
    return StudentProfile(
        nqf_level=data["nqf_level"],
        field_of_study=data["field_of_study"],
        household_income=data["household_income"],
        region=data["region"],
        has_disability=data.get("has_disability", False),
    )
