from django.core.management.base import BaseCommand

from apps.schemes.defaults import DEFAULT_SCHEMES
from apps.schemes.services import SchemeService

class Command(BaseCommand):
    help = "Seed the default Namibian bursary schemes directly into the database (idempotent)."

    def handle(self, *args, **options):
        for name, outcome in SchemeService.seed_defaults(DEFAULT_SCHEMES).items():
            self.stdout.write(f"{'Added' if outcome == 'created' else 'Already exists, skipped'}: {name}")
