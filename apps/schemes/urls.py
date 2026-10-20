from django.urls import path
from .views import SchemeListCreateView

urlpatterns = [path("schemes", SchemeListCreateView.as_view())]
