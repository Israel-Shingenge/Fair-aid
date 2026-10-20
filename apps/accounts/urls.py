from django.urls import path
from . import views

urlpatterns = [
    path("auth/signup", views.SignupView.as_view()),
    path("auth/login", views.LoginView.as_view()),
    path("auth/refresh", views.RefreshView.as_view()),
    path("auth/logout", views.LogoutView.as_view()),
    path("auth/logout-all", views.LogoutAllView.as_view()),
    path("auth/me", views.MeView.as_view()),
    path("users", views.UserListCreateView.as_view()),
    path("users/<int:user_id>", views.UserDetailView.as_view()),
    path("users/<int:user_id>/role", views.UserRoleView.as_view()),
    path("users/<int:user_id>/status", views.UserStatusView.as_view()),
]
