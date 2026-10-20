"""Turns raw rule outcomes into scores and plain-language explanations."""
from typing import List
from .types import LIKELY_ELIGIBLE, POSSIBLY_ELIGIBLE, ChangeSuggestion

def calculate_match_score(total_rules: int, failed_count: int, hard_gate_failed: bool) -> float:
    """Percentage of evaluated criteria met along the path. (Status comes from the leaf, not this.)"""
    if hard_gate_failed:
        return 0.0
    if total_rules == 0:
        return 100.0
    return round(((total_rules - failed_count) / total_rules) * 100, 1)

def _pathways(changes: List[ChangeSuggestion]) -> str:
    return "; ".join(f"{c.criterion} ({c.pathway})" for c in changes)

def generate_plain_language_explanation(
    scheme_name: str,
    match_status: str,
    factors_that_helped: List[str],
    factors_that_hurt: List[str],
    what_would_change_this: List[ChangeSuggestion],
) -> str:
    """Cohesive, encouraging explanation paragraph."""
    sentences: List[str] = []

    if match_status == LIKELY_ELIGIBLE:
        sentences.append(f"You appear likely eligible for the {scheme_name}.")
        if factors_that_helped:
            sentences.append("Factors that helped your match: " + "; ".join(factors_that_helped) + ".")
        sentences.append("No factors hurt your pre-screening eligibility.")

    elif match_status == POSSIBLY_ELIGIBLE:
        sentences.append(f"You are possibly eligible for the {scheme_name}, though there is a minor mismatch.")
        if factors_that_helped:
            sentences.append("Factors that helped: " + "; ".join(factors_that_helped) + ".")
        if factors_that_hurt:
            sentences.append("Factors that hurt: " + "; ".join(factors_that_hurt) + ".")
        if what_would_change_this:
            sentences.append("What could change this: Actionable pathways include " + _pathways(what_would_change_this) + ".")

    else:
        sentences.append(f"You are currently not eligible for the {scheme_name}.")
        if factors_that_hurt:
            sentences.append("Factors that hurt: " + "; ".join(factors_that_hurt) + ".")
        if factors_that_helped:
            sentences.append("Factors that helped: " + "; ".join(factors_that_helped) + ".")
        if what_would_change_this:
            sentences.append("What could change this: Potential future options include " + _pathways(what_would_change_this) + ".")

    return " ".join(sentences)
