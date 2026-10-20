from django.urls import path
from . import views

urlpatterns = [
    path("prescreen/history/<int:record_id>/explain", views.ExplainRunView.as_view()),
    path("prescreen/history/<int:record_id>/ask", views.AskAboutRunView.as_view()),
    path("prescreen/history/<int:record_id>/conversation", views.ConversationView.as_view()),
    path("explanations/quota", views.LLMQuotaStatusView.as_view()),
]
