from django.db import models

class BursaryScheme(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")

    # Core eligibility criteria (null = criterion not applied)
    min_nqf_level = models.IntegerField(null=True, blank=True)
    max_household_income = models.FloatField(null=True, blank=True)
    requires_disability = models.BooleanField(default=False)

    # JSONField is portable across PostgreSQL and SQLite (no dialect-specific ARRAY needed)
    eligible_fields_of_study = models.JSONField(null=True, blank=True)
    eligible_regions = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "bursary_schemes"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name
