from django.urls import path

from .views import DashboardView

urlpatterns = [
    path('staff/dashboard/', DashboardView.as_view()),
]
