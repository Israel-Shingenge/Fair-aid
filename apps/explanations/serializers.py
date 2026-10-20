from rest_framework import serializers

SOURCES = ["llm", "cache", "engine", "fallback"]

class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500, trim_whitespace=True)
    scheme_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)

class SchemeExplanationSerializer(serializers.Serializer):
    scheme_name = serializers.CharField()
    match_status = serializers.CharField(help_text="From the interpretable engine; never written by the LLM")
    match_score = serializers.FloatField()
    explanation = serializers.CharField()
    source = serializers.ChoiceField(choices=["llm", "cache", "fallback"])

class ExplanationResponseSerializer(serializers.Serializer):
    record_id = serializers.IntegerField()
    source = serializers.ChoiceField(choices=["llm", "cache", "fallback"])
    fallback_reason = serializers.CharField(allow_null=True)
    overall_summary = serializers.CharField()
    schemes = SchemeExplanationSerializer(many=True)
    disclaimer = serializers.CharField()

class WhatIfSchemeSerializer(serializers.Serializer):
    scheme_name = serializers.CharField()
    before_status = serializers.CharField()
    after_status = serializers.CharField()
    changed = serializers.BooleanField()

class WhatIfSerializer(serializers.Serializer):
    hypothetical = serializers.BooleanField()
    changes = serializers.DictField(help_text="The validated changes the engine was re-run with")
    schemes = WhatIfSchemeSerializer(many=True)
    note = serializers.CharField()

class AnswerResponseSerializer(serializers.Serializer):
    record_id = serializers.IntegerField()
    turn_id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=["explanation", "what_if"])
    question = serializers.CharField()
    scheme_name = serializers.CharField(allow_null=True)
    match_status = serializers.CharField(allow_null=True, help_text="From the engine; never written by the LLM")
    answer = serializers.CharField()
    what_if = WhatIfSerializer(allow_null=True)
    source = serializers.ChoiceField(choices=SOURCES)
    fallback_reason = serializers.CharField(allow_null=True)
    disclaimer = serializers.CharField()

class ConversationTurnSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    question = serializers.CharField()
    answer = serializers.CharField()
    kind = serializers.CharField()
    scheme_name = serializers.CharField(allow_null=True)
    what_if = WhatIfSerializer(allow_null=True)
    source = serializers.CharField()
