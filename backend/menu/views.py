from django.db.models import Avg, Count, ProtectedError, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import IsCanteenStaff, IsStaffOrReadOnly
from reviews.serializers import ReviewSerializer

from .models import Category, Dish
from .serializers import CategorySerializer, DishAvailabilitySerializer, DishSerializer

TAG = 'Меню'
STAFF_ONLY = ' Только сотрудник столовой.'


@extend_schema_view(
    list=extend_schema(tags=[TAG], summary='Категории', description='Все категории в порядке `order`.'),
    retrieve=extend_schema(tags=[TAG], summary='Одна категория'),
    create=extend_schema(tags=[TAG], summary='Создать категорию', description=STAFF_ONLY),
    update=extend_schema(tags=[TAG], summary='Изменить категорию', description=STAFF_ONLY),
    partial_update=extend_schema(tags=[TAG], summary='Изменить категорию (часть полей)', description=STAFF_ONLY),
    destroy=extend_schema(tags=[TAG], summary='Удалить категорию',
                          description='Категорию с блюдами удалить нельзя — ответ 400.' + STAFF_ONLY),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """Categories: everyone can read, only canteen staff can create, change and delete."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        # Category.dishes uses on_delete=PROTECT: without this the server would answer 500.
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'В категории есть блюда. Сначала перенесите или удалите их.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


DISH_FILTERS = [
    OpenApiParameter('category', OpenApiTypes.INT, description='Только блюда этой категории (id).'),
    OpenApiParameter('search', OpenApiTypes.STR, description='Часть названия, регистр не важен.'),
    OpenApiParameter('available', OpenApiTypes.BOOL,
                     description='`false` — только недоступные (для сотрудника), `true` — только доступные.'),
]
PHOTO_NOTE = ' Фото — файлом в multipart/form-data, до 5 МБ.'


@extend_schema_view(
    list=extend_schema(tags=[TAG], summary='Блюда', parameters=DISH_FILTERS,
                       description='Всё меню, недоступные блюда тоже — с `is_available=false`. '
                                   '`rating` и `reviews_count` — по видимым отзывам.'),
    retrieve=extend_schema(tags=[TAG], summary='Одно блюдо'),
    create=extend_schema(tags=[TAG], summary='Создать блюдо', description=PHOTO_NOTE + STAFF_ONLY),
    update=extend_schema(tags=[TAG], summary='Изменить блюдо', description=PHOTO_NOTE + STAFF_ONLY),
    partial_update=extend_schema(tags=[TAG], summary='Изменить блюдо (часть полей)',
                                 description=PHOTO_NOTE + STAFF_ONLY),
    destroy=extend_schema(tags=[TAG], summary='Удалить блюдо', description=STAFF_ONLY),
)
class DishViewSet(viewsets.ModelViewSet):
    """
    Dishes: everyone can read, only canteen staff can create, change and delete.
    Unavailable dishes are listed too, with is_available=false.
    Filters: ?category=<id>, ?search=<part of the name>, ?available=true|false.
    """

    serializer_class = DishSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        # The average rating and the number of reviews count only visible reviews.
        visible = Q(reviews__is_visible=True)
        queryset = Dish.objects.select_related('category').annotate(
            rating=Avg('reviews__rating', filter=visible),
            reviews_count=Count('reviews', filter=visible),
        )
        params = self.request.query_params

        category = params.get('category')
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)

        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(search_name__contains=search.lower())

        # ?available=false — only dishes that are not available (for the staff panel), ?available=true — only available.
        available = params.get('available', '').lower()
        if available in ('true', 'false'):
            queryset = queryset.filter(is_available=available == 'true')

        return queryset

    @extend_schema(tags=[TAG], summary='Переключить наличие', request=DishAvailabilitySerializer,
                   responses=DishSerializer, description='Только поле `is_available`.' + STAFF_ONLY)
    @action(detail=True, methods=['patch'], permission_classes=[IsCanteenStaff],
            serializer_class=DishAvailabilitySerializer)
    def availability(self, request, pk=None):
        """PATCH /api/dishes/{id}/availability/ {is_available} — quickly mark a dish as there / not there."""
        dish = self.get_object()
        # In form data DRF treats a missing checkbox as False; require the field explicitly.
        if 'is_available' not in request.data:
            return Response({'is_available': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DishAvailabilitySerializer(dish, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DishSerializer(dish, context=self.get_serializer_context()).data)

    @extend_schema(tags=[TAG], summary='Отзывы о блюде', responses=ReviewSerializer(many=True),
                   description='Только видимые отзывы, новые сначала. Список страницами.')
    @action(detail=True, methods=['get'], permission_classes=[AllowAny], serializer_class=ReviewSerializer)
    def reviews(self, request, pk=None):
        """GET /api/dishes/{id}/reviews/ — visible reviews of the dish, newest first."""
        dish = self.get_object()
        reviews = dish.reviews.filter(is_visible=True).select_related('user', 'dish')
        page = self.paginate_queryset(reviews)
        serializer = ReviewSerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)
