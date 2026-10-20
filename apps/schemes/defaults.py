"""
Default Bursary Scheme Definitions: the single source of truth for the benchmark Namibian schemes.

Used by the ``seed_schemes`` management command and by the fairness audit's in-memory benchmark.
Plain data only, so it can be imported without Django being ready.
"""
from typing import Any, Dict, List

DEFAULT_SCHEMES: List[Dict[str, Any]] = [
    {
        "name": "NSFAF Core Grant",
        "description": "Namibia Students Financial Assistance Fund core grant for undergraduate students.",
        "min_nqf_level": 6,
        "max_household_income": 500000.0,
        "requires_disability": False,
        "eligible_fields_of_study": None,
        "eligible_regions": None,
    },
    {
        "name": "MTC Tech Innovation Bursary",
        "description": "Bursary for outstanding students in technology, IT, and engineering.",
        "min_nqf_level": 7,
        "max_household_income": None,
        "requires_disability": False,
        "eligible_fields_of_study": [
            "Computer Science",
            "Information Technology",
            "Software Engineering",
            "Telecommunications",
        ],
        "eligible_regions": None,
    },
    {
        "name": "O&L Regional Development Fund",
        "description": "Targeted support for students from specific regions studying agriculture and commerce.",
        "min_nqf_level": 5,
        "max_household_income": 300000.0,
        "requires_disability": False,
        "eligible_fields_of_study": ["Agriculture", "Commerce", "Business Administration"],
        "eligible_regions": ["Erongo", "Oshikoto", "Karas"],
    },
    {
        "name": "Namdeb STEM Bursary",
        "description": "Full bursary for engineering and science students with excellent academic records.",
        "min_nqf_level": 7,
        "max_household_income": None,
        "requires_disability": False,
        "eligible_fields_of_study": [
            "Mining Engineering",
            "Metallurgy",
            "Geology",
            "Mechanical Engineering",
        ],
        "eligible_regions": None,
    },
    {
        "name": "Ministry of Disability Affairs Scholarship",
        "description": "Specialized support for students with recognized disabilities across all fields.",
        "min_nqf_level": 5,
        "max_household_income": 400000.0,
        "requires_disability": True,
        "eligible_fields_of_study": None,
        "eligible_regions": None,
    },
]
