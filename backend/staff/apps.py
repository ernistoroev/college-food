from django.apps import AppConfig


class StaffConfig(AppConfig):
    """Canteen staff panel: endpoints that combine data from menu, orders and reviews. No models."""

    name = 'staff'
    verbose_name = 'панель сотрудника'
