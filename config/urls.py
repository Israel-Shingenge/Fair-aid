from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.common.views import RootView

api_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.schemes.urls")),
    path("", include("apps.prescreening.urls")),
    path("", include("apps.fairness.urls")),
    path("", include("apps.governance.urls")),
    path("", include("apps.explanations.urls")),
]

urlpatterns = [
    path("", RootView.as_view()),
    path("admin/", admin.site.urls),
    path("openapi.json", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema")),
    path(f"{settings.API_V1_PREFIX.strip('/')}/", include(api_patterns)),
]
