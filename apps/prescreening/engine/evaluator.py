"""Walks a compiled decision tree for one student and assembles the explained result."""
from __future__ import annotations
from typing import List, Optional
from .explainer import calculate_match_score, generate_plain_language_explanation
from .rules import DEFAULT_RULES
from .rules.base import EligibilityRule
from .tree import DecisionNode, TreeNode, build_tree
from .types import (
    ChangeSuggestion,
    DecisionPathStep,
    MatchExplanation,
    SchemeCriteria,
    SchemeMatchResult,
    StudentProfile,
)

class BursaryDecisionTree:
    def __init__(self, scheme: SchemeCriteria, rules: Optional[List[EligibilityRule]] = None):
        self.scheme = scheme
        self.rules = rules if rules is not None else DEFAULT_RULES
        applicable = [rule for rule in self.rules if rule.is_applicable(scheme)]
        self.root: TreeNode = build_tree(applicable)

    def evaluate(self, student: StudentProfile) -> SchemeMatchResult:
        path: List[DecisionPathStep] = []
        explanations: List[MatchExplanation] = []
        actionable_feedback: List[str] = []
        changes: List[ChangeSuggestion] = []
        helped: List[str] = []
        hurt: List[str] = []
        failed_count = 0
        total_rules = 0
        hard_gate_failed = False

        node: TreeNode = self.root
        while isinstance(node, DecisionNode):
            rule = node.rule
            outcome = rule.evaluate(student, self.scheme)
            total_rules += 1

            path.append(DecisionPathStep(total_rules, rule.name, rule.condition_desc, outcome.passed, outcome.details))
            explanations.append(MatchExplanation(rule.name, outcome.passed, outcome.details))

            if outcome.passed:
                helped.append(f"{rule.name}: {outcome.details}")
            else:
                hurt.append(f"{rule.name}: {outcome.details}")
                failed_count += 1
                if outcome.change:
                    actionable_feedback.append(outcome.change.suggestion)
                    changes.append(outcome.change)
                if rule.is_hard_gate:
                    hard_gate_failed = True

            node = node.true_branch if outcome.passed else node.false_branch

        return SchemeMatchResult(
            scheme_name=self.scheme.name,
            description=self.scheme.description,
            match_status=node.match_status,
            match_score=calculate_match_score(total_rules, failed_count, hard_gate_failed),
            plain_language_explanation=generate_plain_language_explanation(
                self.scheme.name, node.match_status, helped, hurt, changes
            ),
            factors_that_helped=helped,
            factors_that_hurt=hurt,
            what_would_change_this=changes,
            decision_path=path,
            explanations=explanations,
            actionable_feedback=actionable_feedback,
        )

def evaluate_scheme(student: StudentProfile, scheme: SchemeCriteria) -> SchemeMatchResult:
    """Convenience entry point: compile the tree for ``scheme`` and evaluate ``student``."""
    return BursaryDecisionTree(scheme).evaluate(student)
