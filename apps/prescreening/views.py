from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent

from . import serializers as s
from .adapters import profile_from_validated
from .services import PrescreenService

TAGS = ["Pre-Screening"]


class PrescreenView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(request=s.StudentCircumstancesSerializer, responses=s.SchemeMatchResultSerializer(many=True),
                   tags=TAGS, summary="Evaluate student circumstances against bursary schemes (student)")
    def post(self, request):
        """Evaluates against all schemes with the interpretable decision tree; the run is saved to history."""
        serializer = s.StudentCircumstancesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        results = PrescreenService.evaluate_and_record(profile_from_validated(serializer.validated_data), request.user)
        return Response(s.SchemeMatchResultSerializer(results, many=True).data)


class PrescreenHistoryView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=s.PrescreenRecordSerializer(many=True), tags=TAGS,
                   summary="List my previous pre-screening runs (student)")
    def get(self, request):
        return Response(s.PrescreenRecordSerializer(PrescreenService.get_history(request.user), many=True).data)
