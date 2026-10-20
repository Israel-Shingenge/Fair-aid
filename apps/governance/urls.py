from django.urls import path
from . import views

urlpatterns = [
    path("governance/safeguards", views.SafeguardPoliciesView.as_view()),
    path("applications/submit", views.ApplicationSubmitGuardView.as_view()),
    path("decisions/award", views.AwardDecisionGuardView.as_view()),
]
