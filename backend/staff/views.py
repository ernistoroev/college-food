from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCanteenStaff
from menu.models import Dish
from orders.models import Order
from reviews.models import Review
from reviews.serializers import ReviewSerializer

LATEST_REVIEWS = 5


class DashboardSerializer(serializers.Serializer):
    """The answer of the dashboard (only for the API documentation)."""

    dishes_total = serializers.IntegerField(help_text='Всего блюд в меню.')
    dishes_unavailable = serializers.IntegerField(help_text='Блюд с is_available=false.')
    dishes_sold_out = serializers.IntegerField(help_text='В наличии, но порций на сегодня 0.')
    orders_new = serializers.IntegerField(help_text='Заказов в статусе «Новый».')
    orders_cooking = serializers.IntegerField(help_text='Заказов в статусе «Готовится».')
    orders_ready = serializers.IntegerField(help_text='Заказов в статусе «Готов».')
    latest_reviews = ReviewSerializer(many=True, help_text='5 последних отзывов, и скрытые тоже.')


class DashboardView(APIView):
    """
    GET /api/staff/dashboard/ — numbers for the first screen of the staff panel.
    Latest reviews include hidden ones (is_visible=false), so staff can moderate them.
    """

    permission_classes = [IsCanteenStaff]

    @extend_schema(tags=['Сотрудник'], summary='Сводка для панели сотрудника', responses=DashboardSerializer,
                   description='Только сотрудник столовой.')
    def get(self, request):
        dishes = Dish.objects.all()
        orders = Order.objects.all()
        reviews = Review.objects.select_related('user', 'dish')[:LATEST_REVIEWS]

        return Response({
            'dishes_total': dishes.count(),
            'dishes_unavailable': dishes.filter(is_available=False).count(),
            # Available, but the portions for today are over — time to cook more.
            'dishes_sold_out': dishes.filter(is_available=True, portions_today=0).count(),
            'orders_new': orders.filter(status=Order.Status.NEW).count(),
            'orders_cooking': orders.filter(status=Order.Status.COOKING).count(),
            'orders_ready': orders.filter(status=Order.Status.READY).count(),
            'latest_reviews': ReviewSerializer(reviews, many=True, context={'request': request}).data,
        })
