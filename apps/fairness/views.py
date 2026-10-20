from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsStaff
from .services import FairnessService

class FairnessAuditView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        summary="Execute algorithmic fairness audit across demographic groups (admin / superuser)",
        parameters=[
            OpenApiParameter("n_applicants", int, description="Size of synthetic cohort (50-2000)", default=300),
            OpenApiParameter("seed", int, description="Random seed for reproducible sampling", default=42),
        ],
        responses={200: OpenApiTypes.OBJECT},
        tags=["Fairness Audit"],
    )
    def get(self, request):
        try:
            n_applicants = int(request.query_params.get("n_applicants", 300))
            seed = int(request.query_params.get("seed", 42))
        except ValueError:
            return Response({"detail": "n_applicants and seed must be integers"}, status=400)
        if not 50 <= n_applicants <= 2000:
            return Response({"detail": "n_applicants must be between 50 and 2000"}, status=400)
        return Response(FairnessService.audit_demographic_fairness(n_applicants=n_applicants, seed=seed))
