from rest_framework import serializers
from .models import BursaryScheme

class BursarySchemeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(allow_blank=True)
    eligible_fields_of_study = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    eligible_regions = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)

    class Meta:
        model = BursaryScheme
        fields = [
            "id", "name", "description", "min_nqf_level", "max_household_income",
            "requires_disability", "eligible_fields_of_study", "eligible_regions",
        ]
        read_only_fields = ["id"]
        # uniqueness is reported by the service as a 409 Conflict, as before
        extra_kwargs = {"name": {"validators": []}}
