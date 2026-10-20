from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaff

from .serializers import BursarySchemeSerializer
from .services import SchemeService

TAGS = ["Bursary Schemes"]


class SchemeListCreateView(APIView):
    def get_permissions(self):
        return [IsStaff()] if self.request.method == "POST" else []

    @extend_schema(responses=BursarySchemeSerializer(many=True), tags=TAGS, summary="List all registered bursary schemes")
    def get(self, request):
        return Response(BursarySchemeSerializer(SchemeService.get_all_schemes(), many=True).data)

    @extend_schema(request=BursarySchemeSerializer, responses={201: BursarySchemeSerializer}, tags=TAGS,
                   summary="Register a new bursary scheme (admin / superuser)")
    def post(self, request):
        serializer = BursarySchemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scheme = SchemeService.create_scheme(serializer.validated_data)
        return Response(BursarySchemeSerializer(scheme).data, status=status.HTTP_201_CREATED)
