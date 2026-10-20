"""Human-in-the-loop policy: what FairAid will and will not do. Framework-free."""
from typing import Any, Dict, List
from apps.common.exceptions import AutomatedActionBlocked

class HumanInTheLoopPolicy:
    SYSTEM_ROLE: str = "Advisory Pre-Screening & Student Informational Tool"
    IS_BINDING_DECISION: bool = False
    HCAI_ZONE: str = "High Human Control + High Machine Automation"
    ALLOWS_AUTOMATED_SUBMISSION: bool = False
    FINAL_DECISION_AUTHORITY: str = "Human Bursary Committees & Institutional Scholarship Officers"

    LEGAL_DISCLAIMER: str = (
        "ADVISORY NOTICE: FairAid is a pre-screening and "
        "informational tool. It does NOT submit applications on your behalf, nor does it make "
        "final funding commitments. All final awards require official certified document "
        "verification and human review by authorised bursary trustees."
    )

    ACTIONABLE_HUMAN_STEPS: List[str] = [
        "Review your generated pre-screening report and suggestions.",
        "Gather officially certified documentation (certified ID, police declarations, academic transcripts, proof of household income).",
        "Log in directly to the official fund portal (e.g., NSFAF online portal or corporate sponsor website).",
        "Submit your completed application personally or online before the deadline.",
        "Provide supplementary documentation requested by human bursary officers.",
    ]

    PRINCIPLES_APPLIED: List[str] = [
        "Preservation of Applicant Moral Agency",
        "Human Accountability Chain",
        "Prohibition of Solely Automated Legal Adjudication",
        "Fraud Prevention & Physical Evidence Auditability",
    ]

    @classmethod
    def get_governance_metadata(cls) -> Dict[str, Any]:
        return {
            "system_role": cls.SYSTEM_ROLE,
            "is_binding_decision": cls.IS_BINDING_DECISION,
            "hcai_framework_zone": cls.HCAI_ZONE,
            "allows_automated_submission": cls.ALLOWS_AUTOMATED_SUBMISSION,
            "final_decision_authority": cls.FINAL_DECISION_AUTHORITY,
            "mandatory_disclaimer": cls.LEGAL_DISCLAIMER,
            "student_submission_checklist": cls.ACTIONABLE_HUMAN_STEPS,
            "principles_applied": cls.PRINCIPLES_APPLIED,
        }

    @classmethod
    def block_automated_submission(cls, action_name: str = "submit_application") -> None:
        raise AutomatedActionBlocked(
            f"Action '{action_name}' is blocked by the FairAid Human-in-the-Loop Safeguard.",
            details={
                "detail": {
                    "error": "Automated Action Prohibited",
                    "message": (
                        f"Action '{action_name}' is blocked by the FairAid Human-in-the-Loop Safeguard. "
                        "The system is architecturally restricted to pre-screening and informational assistance. "
                        "All application submissions and funding awards must be executed manually by human agents."
                    ),
                    "hcai_governance": cls.get_governance_metadata(),
                }
            },
        )
