from rest_framework import serializers

from .models import PrescreenRecord


class StudentCircumstancesSerializer(serializers.Serializer):
    nqf_level = serializers.IntegerField(help_text="Current NQF level of the student")
    field_of_study = serializers.CharField(help_text="Field of study")
    household_income = serializers.FloatField(help_text="Total annual household income in NAD")
    region = serializers.CharField(help_text="Region of residence")
    has_disability = serializers.BooleanField(default=False, help_text="Whether the student has a recognised disability")


class MatchExplanationSerializer(serializers.Serializer):
    criterion = serializers.CharField()
    is_met = serializers.BooleanField()
    message = serializers.CharField()


class DecisionPathStepSerializer(serializers.Serializer):
    step = serializers.IntegerField()
    rule = serializers.CharField()
    condition = serializers.CharField()
    passed = serializers.BooleanField()
    details = serializers.CharField()


class ChangeSuggestionSerializer(serializers.Serializer):
    criterion = serializers.CharField(help_text="The criterion that caused the mismatch")
    current_circumstance = serializers.CharField()
    required_to_qualify = serializers.CharField()
    pathway = serializers.CharField()
    suggestion = serializers.CharField()


class SchemeMatchResultSerializer(serializers.Serializer):
    scheme_name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    match_status = serializers.CharField()
    match_score = serializers.FloatField()
    plain_language_explanation = serializers.CharField()
    factors_that_helped = serializers.ListField(child=serializers.CharField())
    factors_that_hurt = serializers.ListField(child=serializers.CharField())
    what_would_change_this = ChangeSuggestionSerializer(many=True)
    decision_path = DecisionPathStepSerializer(many=True)
    explanations = MatchExplanationSerializer(many=True)
    actionable_feedback = serializers.ListField(child=serializers.CharField())
    is_binding_decision = serializers.BooleanField()
    allows_automated_submission = serializers.BooleanField()
    governance_safeguard = serializers.CharField()


class PrescreenRecordSerializer(serializers.ModelSerializer):
    circumstances = StudentCircumstancesSerializer(read_only=True)
    results = SchemeMatchResultSerializer(many=True, read_only=True)

    class Meta:
        model = PrescreenRecord
        fields = ["id", "created_at", "circumstances", "results"]
