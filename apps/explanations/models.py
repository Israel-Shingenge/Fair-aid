from django.db import models
from django.utils import timezone

class LLMGate(models.Model):
    """
    Single-row, cross-process rate limiter for the LLM provider (id is always 1).

    * ``next_slot_at``  no new request may start before this instant (also a lease while one is in flight).
    * ``requests_today`` / ``window_date``  daily budget, counted per Pacific-time day (Google's reset).
    * ``blocked_until``  set after a 429 from the provider.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    next_slot_at = models.DateTimeField(default=timezone.now)
    window_date = models.DateField(null=True, blank=True)
    requests_today = models.PositiveIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    block_reason = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        db_table = "llm_gate"

class ExplanationCache(models.Model):
    """
    Validated LLM output keyed by a hash of (prompt version, model, engine facts, question).
    Identical facts give identical answers, so repeat views and same-profile students cost no quota.
    """

    key = models.CharField(max_length=64, primary_key=True)
    kind = models.CharField(max_length=16)  # "explain" | "ask"
    payload = models.JSONField()
    model = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_explanation_cache"

class ConversationTurn(models.Model):
    """
    One question and the answer the student was shown, stored on the server so follow-ups have context.
    Memory is server-side on purpose: a client can't plant fake "earlier answers" into the model's prompt.
    """

    record = models.ForeignKey("prescreening.PrescreenRecord", on_delete=models.CASCADE, related_name="conversation_turns")
    question = models.TextField()
    answer = models.TextField()
    kind = models.CharField(max_length=16, default="explanation")  # "explanation" | "what_if"
    scheme_name = models.CharField(max_length=255, null=True, blank=True)
    what_if = models.JSONField(null=True, blank=True)
    source = models.CharField(max_length=16, default="fallback")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_conversation_turns"
        ordering = ["id"]
