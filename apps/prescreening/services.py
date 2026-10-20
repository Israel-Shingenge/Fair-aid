"""Orchestrates evaluating a student against every registered scheme and recording the run."""
import dataclasses
from typing import List

from apps.accounts.models import User
from apps.governance.safeguards import HumanInTheLoopPolicy
from apps.schemes.services import SchemeService

from .adapters import scheme_to_criteria
from .engine import SchemeMatchResult, StudentProfile, evaluate_scheme
from .models import PrescreenRecord
from .serializers import SchemeMatchResultSerializer, StudentCircumstancesSerializer


class PrescreenService:
    @staticmethod
    def evaluate_student(student: StudentProfile) -> List[SchemeMatchResult]:
        """Evaluate against all schemes and stamp each result with the mandatory advisory metadata."""
        results = []
        for scheme in SchemeService.get_all_schemes():
            result = evaluate_scheme(student, scheme_to_criteria(scheme))
            results.append(
                dataclasses.replace(
                    result,
                    is_binding_decision=HumanInTheLoopPolicy.IS_BINDING_DECISION,
                    allows_automated_submission=HumanInTheLoopPolicy.ALLOWS_AUTOMATED_SUBMISSION,
                    governance_safeguard=HumanInTheLoopPolicy.LEGAL_DISCLAIMER,
                )
            )
        return results

    @staticmethod
    def evaluate_and_record(student: StudentProfile, user: User) -> List[SchemeMatchResult]:
        results = PrescreenService.evaluate_student(student)
        PrescreenRecord.objects.create(
            user=user,
            circumstances=StudentCircumstancesSerializer(dataclasses.asdict(student)).data,
            results=SchemeMatchResultSerializer(results, many=True).data,
        )
        return results

    @staticmethod
    def get_history(user: User) -> List[PrescreenRecord]:
        return list(PrescreenRecord.objects.filter(user=user))
