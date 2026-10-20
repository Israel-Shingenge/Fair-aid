from typing import Any, Dict, List
from django.db import IntegrityError, transaction
from apps.common.exceptions import ConflictError
from .models import BursaryScheme

class SchemeService:
    @staticmethod
    def get_all_schemes() -> List[BursaryScheme]:
        return list(BursaryScheme.objects.all())

    @staticmethod
    def create_scheme(data: Dict[str, Any]) -> BursaryScheme:
        try:
            with transaction.atomic():
                return BursaryScheme.objects.create(**data)
        except IntegrityError as exc:
            raise ConflictError(f"A scheme named '{data['name']}' already exists") from exc

    @staticmethod
    def seed_defaults(schemes: List[Dict[str, Any]]) -> Dict[str, str]:
        """Insert any scheme not already present (matched by name). Returns {name: 'created'|'skipped'}."""
        report = {}
        for data in schemes:
            _, created = BursaryScheme.objects.get_or_create(name=data["name"], defaults=data)
            report[data["name"]] = "created" if created else "skipped"
        return report
