from django.urls import path

from . import views

urlpatterns = [
    path("prescreen", views.PrescreenView.as_view()),
    path("prescreen/history", views.PrescreenHistoryView.as_view()),
]
