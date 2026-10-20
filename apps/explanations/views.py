from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaff, IsStudent
from apps.common.exceptions import NotFoundError
from apps.prescreening.models import PrescreenRecord

from . import serializers as s
from .service import ExplanationService

TAGS = ["Explanations (LLM)"]

def _own_record(user, record_id: int) -> PrescreenRecord:
    record = PrescreenRecord.objects.filter(pk=record_id, user=user).first()
    if record is None:
        raise NotFoundError(f"Pre-screening run {record_id} not found")
    return record

class ExplainRunView(APIView):
    permission_classes = [IsStudent]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "llm_explain"

    @extend_schema(request=None, responses=s.ExplanationResponseSerializer, tags=TAGS,
                   summary="Conversational explanation of a saved pre-screening run (student)")
    def post(self, request, record_id: int):
        """
        Plain-language explanation of each scheme's result. The LLM only rephrases the engine's factors;
        `match_status` always comes from the engine. Falls back to the engine's own wording when the LLM
        is unavailable (see `source` / `fallback_reason`).
        """
        record = _own_record(request.user, record_id)
        return Response(s.ExplanationResponseSerializer(ExplanationService().explain_run(record)).data)

class AskAboutRunView(APIView):
    permission_classes = [IsStudent]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "llm_ask"

    @extend_schema(request=s.AskSerializer, responses=s.AnswerResponseSerializer, tags=TAGS,
                   summary='Ask a follow-up, e.g. "Why wasn\'t I matched to Scheme X?" (student)')
    def post(self, request, record_id: int):
        data = s.AskSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        record = _own_record(request.user, record_id)
        result = ExplanationService().answer_question(
            record, data.validated_data["question"], data.validated_data.get("scheme_name") or None
        )
        return Response(s.AnswerResponseSerializer(result).data)

class ConversationView(APIView):
    permission_classes = [IsStudent]

    @extend_schema(responses=s.ConversationTurnSerializer(many=True), tags=TAGS,
                   summary="Follow-up conversation so far for a saved run (student)")
    def get(self, request, record_id: int):
        record = _own_record(request.user, record_id)
        return Response(s.ConversationTurnSerializer(ExplanationService().conversation(record), many=True).data)

    @extend_schema(responses={204: None}, tags=TAGS, summary="Clear the follow-up conversation for a run (student)")
    def delete(self, request, record_id: int):
        ExplanationService().reset_conversation(_own_record(request.user, record_id))
        return Response(status=204)

class LLMQuotaStatusView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=TAGS, summary="LLM quota usage (admin / superuser)")
    def get(self, request):
        return Response(ExplanationService().quota_status())
