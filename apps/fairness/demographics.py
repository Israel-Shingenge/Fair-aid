"""
Synthetic applicant cohort reflecting Namibian demographics:
~40% urban (Khomas, Erongo), ~60% rural/peripheral; ~10% students with recognised disabilities.
"""
import random
from typing import Any, Dict, List

from apps.prescreening.engine import StudentProfile

URBAN_REGIONS = ["Khomas", "Erongo"]
RURAL_REGIONS = [
    "Kavango East", "Kavango West", "Zambezi", "Kunene",
    "Ohangwena", "Omaheke", "Omusati", "Oshana", "Oshikoto", "Hardap", "Karas",
]
ALL_FIELDS = [
    "Computer Science", "Information Technology", "Software Engineering",
    "Mining Engineering", "Mechanical Engineering", "Civil Engineering",
    "Agriculture", "Commerce", "Business Administration",
    "Education", "Nursing", "Humanities",
]
_URBAN_BIASED_FIELDS = [
    "Computer Science", "Information Technology", "Software Engineering",
    "Mining Engineering", "Mechanical Engineering",
]


def generate_synthetic_applicants(n: int = 300, seed: int = 42) -> List[Dict[str, Any]]:
    # NOTE: the sequence of rng calls below is part of the contract: it makes audits reproducible
    # for a given seed, so do not reorder them.
    rng = random.Random(seed)
    applicants = []

    for i in range(n):
        is_rural = rng.random() < 0.60
        if is_rural:
            region = rng.choice(RURAL_REGIONS)
            household_income = round(rng.uniform(30000, 280000), 2)
            nqf_level = rng.choices([5, 6, 7, 8], weights=[0.40, 0.35, 0.20, 0.05])[0]
        else:
            region = rng.choice(URBAN_REGIONS)
            household_income = round(rng.uniform(60000, 650000), 2)
            nqf_level = rng.choices([5, 6, 7, 8], weights=[0.15, 0.30, 0.45, 0.10])[0]

        has_disability = rng.random() < 0.10
        gender = "Female" if rng.random() < 0.52 else "Male"

        if not is_rural and rng.random() < 0.50:
            field = rng.choice(_URBAN_BIASED_FIELDS)
        else:
            field = rng.choice(ALL_FIELDS)

        applicants.append(
            {
                "applicant_id": f"APP-{i + 1:04d}",
                "gender": gender,
                "is_rural": is_rural,
                "region_type": "Rural" if is_rural else "Urban",
                "circumstances": StudentProfile(
                    nqf_level=nqf_level,
                    field_of_study=field,
                    household_income=household_income,
                    region=region,
                    has_disability=has_disability,
                ),
            }
        )
    return applicants
