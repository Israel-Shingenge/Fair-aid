from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.governance.safeguards import HumanInTheLoopPolicy

class RootView(APIView):
    """System health status and the explicit HCAI operational-zone notice."""

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["System Information"])
    def get(self, request):
        return Response(
            {
                "system": "FairAid Pre-Screening API",
                "status": "online",
                "docs_url": "/docs",
                "hcai_zone": HumanInTheLoopPolicy.HCAI_ZONE,
                "is_binding_decision": HumanInTheLoopPolicy.IS_BINDING_DECISION,
                "allows_automated_submission": HumanInTheLoopPolicy.ALLOWS_AUTOMATED_SUBMISSION,
                "notice": HumanInTheLoopPolicy.LEGAL_DISCLAIMER,
            }
        )
