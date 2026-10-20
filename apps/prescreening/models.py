from django.conf import settings
from django.db import models


class PrescreenRecord(models.Model):
    """A saved pre-screening run so students can review their history."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescreen_records")
    created_at = models.DateTimeField(auto_now_add=True)
    # Snapshot of what the student submitted and what the engine returned at that time
    circumstances = models.JSONField()
    results = models.JSONField()

    class Meta:
        db_table = "prescreen_records"
        ordering = ["-created_at", "-id"]
