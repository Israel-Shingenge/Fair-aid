"""
Decision-tree structure and construction.

A scheme's applicable rules are compiled into an explicit binary tree:

* ``DecisionNode`` tests exactly one rule (``true_branch`` on pass, ``false_branch`` on fail).
* ``LeafNode`` holds the final outcome.

A failed hard gate leads straight to a "Not eligible" leaf. Every other rule is still evaluated on
both branches so the student gets complete feedback; each subtree remembers how many soft criteria
have failed so far (0, 1 or 2+) and its leaves carry the matching outcome:
0 failures -> Likely eligible, 1 -> Possibly eligible, 2+ -> Not eligible.

The tree is fully expanded, so it has at most 2^(n+1) - 1 nodes for n applicable rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from .rules.base import EligibilityRule
from .types import LIKELY_ELIGIBLE, NOT_ELIGIBLE, POSSIBLY_ELIGIBLE

# Beyond this many soft failures the outcome no longer changes ("Not eligible").
MAX_TRACKED_FAILURES = 2

@dataclass(frozen=True)
class LeafNode:
    match_status: str
    reason: str


@dataclass(frozen=True)
class DecisionNode:
    rule: EligibilityRule
    true_branch: "TreeNode"
    false_branch: "TreeNode"

TreeNode = Union[DecisionNode, LeafNode]

def _outcome_leaf(failures_so_far: int) -> LeafNode:
    if failures_so_far == 0:
        return LeafNode(LIKELY_ELIGIBLE, "All applicable criteria met")
    if failures_so_far == 1:
        return LeafNode(POSSIBLY_ELIGIBLE, "Exactly one soft criterion not met")
    return LeafNode(NOT_ELIGIBLE, "Two or more soft criteria not met")

def build_tree(rules: List[EligibilityRule], failures_so_far: int = 0) -> TreeNode:
    """Recursively build the subtree for ``rules`` given the soft failures already on the path."""
    if not rules:
        return _outcome_leaf(failures_so_far)

    rule, remaining = rules[0], rules[1:]
    true_branch = build_tree(remaining, failures_so_far)

    if rule.is_hard_gate:
        false_branch: TreeNode = LeafNode(NOT_ELIGIBLE, f"Hard gate not met: {rule.name}")
    else:
        false_branch = build_tree(remaining, min(failures_so_far + 1, MAX_TRACKED_FAILURES))

    return DecisionNode(rule, true_branch, false_branch)
