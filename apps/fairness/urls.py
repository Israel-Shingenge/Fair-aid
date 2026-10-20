from django.urls import path
from .views import FairnessAuditView

urlpatterns = [path("fairness/audit", FairnessAuditView.as_view())]
