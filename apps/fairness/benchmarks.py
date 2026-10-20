from typing import List
from apps.prescreening.engine import SchemeCriteria
from apps.schemes.defaults import DEFAULT_SCHEMES

def _tuple_or_none(values):
    return tuple(values) if values else None

def get_default_schemes() -> List[SchemeCriteria]:
    """In-memory benchmark schemes; never touches the database."""
    return [
        SchemeCriteria(
            name=s["name"],
            description=s["description"],
            min_nqf_level=s["min_nqf_level"],
            max_household_income=s["max_household_income"],
            requires_disability=s["requires_disability"],
            eligible_fields_of_study=_tuple_or_none(s["eligible_fields_of_study"]),
            eligible_regions=_tuple_or_none(s["eligible_regions"]),
        )
        for s in DEFAULT_SCHEMES
    ]
