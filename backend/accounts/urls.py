from django.urls import path

from .views import LoginView, MeView, RefreshView, RegisterView

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    # {refresh} -> {access}: a new access token when the old one has expired.
    path('auth/refresh/', RefreshView.as_view()),
    path('auth/me/', MeView.as_view()),
]
