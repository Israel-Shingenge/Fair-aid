from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .safeguards import HumanInTheLoopPolicy
from .serializers import GovernanceMetadataSerializer

class SafeguardPoliciesView(APIView):
    """HCAI governance declarations, legal disclaimers and the manual application checklist."""

    @extend_schema(responses=GovernanceMetadataSerializer, tags=["Governance & Safeguards"])
    def get(self, request):
        return Response(GovernanceMetadataSerializer(HumanInTheLoopPolicy.get_governance_metadata()).data)

class _BlockedActionView(APIView):
    """Refusal guardrail: always HTTP 403."""

    action_name: str = ""

    @extend_schema(request=None, responses={403: OpenApiTypes.OBJECT}, tags=["Governance & Safeguards"])
    def post(self, request):
        HumanInTheLoopPolicy.block_automated_submission(action_name=self.action_name)

class ApplicationSubmitGuardView(_BlockedActionView):
    """Blocks any automated attempt to submit a bursary application."""

    action_name = "automated_application_submission"

class AwardDecisionGuardView(_BlockedActionView):
    """Blocks any automated attempt to make a binding funding award."""

    action_name = "automated_funding_award"
