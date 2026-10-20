from rest_framework import serializers

class GovernanceMetadataSerializer(serializers.Serializer):
    system_role = serializers.CharField()
    hcai_framework_zone = serializers.CharField()
    is_binding_decision = serializers.BooleanField()
    allows_automated_submission = serializers.BooleanField()
    final_decision_authority = serializers.CharField()
    mandatory_disclaimer = serializers.CharField()
    student_submission_checklist = serializers.ListField(child=serializers.CharField())
    principles_applied = serializers.ListField(child=serializers.CharField())
