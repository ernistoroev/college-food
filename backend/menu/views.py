from rest_framework import viewsets

from .models import Category, Dish
from .serializers import CategorySerializer, DishSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class DishViewSet(viewsets.ReadOnlyModelViewSet):
    """Блюда в наличии. Фильтр по категории: ?category=<id>."""

    serializer_class = DishSerializer

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True).select_related('category')
        category = self.request.query_params.get('category')
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)
        return queryset
