from django.urls import path

from .views import LoginView, StaffLoginView, MeView, RefreshView, RegisterView

urlpatterns = [
    path('staff/auth/login/', StaffLoginView.as_view()),
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    # {refresh} -> {access}: a new access token when the old one has expired.
    path('auth/refresh/', RefreshView.as_view()),
    path('auth/me/', MeView.as_view()),
]
