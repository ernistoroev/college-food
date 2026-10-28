from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsCanteenStaff, IsStudent, is_canteen_staff

from .models import Order
from .serializers import (
    MessageSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    StaffOrderDetailSerializer,
)

TAG = 'Заказы'


@extend_schema_view(
    list=extend_schema(
        tags=[TAG], summary='Заказы', description='Студент видит свои заказы, сотрудник — все. Новые сначала.',
        parameters=[OpenApiParameter('status', OpenApiTypes.STR, enum=Order.Status.values,
                                     description='Только заказы в этом статусе.')],
    ),
    retrieve=extend_schema(
        tags=[TAG], summary='Один заказ', responses=StaffOrderDetailSerializer,
        description='Сотруднику — с контактами студента (`customer_name`, `customer_email`). '
                    'Чужой заказ для студента — 404.',
    ),
    create=extend_schema(
        tags=[TAG], summary='Оформить заказ', request=OrderCreateSerializer, responses={201: OrderSerializer},
        description='Только студент. Сумму считает сервер по ценам из базы; если порций не хватает — 400 '
                    'и ничего не списывается.',
    ),
    change_status=extend_schema(
        tags=[TAG], summary='Сменить статус', request=OrderStatusSerializer, responses=StaffOrderDetailSerializer,
        description='Только сотрудник. «Выдан» и «Отменён» — финальные; при отмене порции возвращаются в меню.',
    ),
)

class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/orders/                — a student sees own orders, staff see all; filter ?status=new;
    POST  /api/orders/                — a student places an order {student_name, pickup_time, comment?, items};
    GET   /api/orders/{id}/           — one order (for staff with the student's contacts);
    PATCH /api/orders/{id}/status/    — staff change the status {status};
    GET   /api/orders/{id}/messages/  — chat about the order; POST {text} — send a message.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related('items')
        if getattr(self, 'swagger_fake_view', False):  # the API documentation is being built
            return queryset
        # A student sees only own orders; for someone else's order the answer is 404.
        if not is_canteen_staff(self.request.user):
            queryset = queryset.filter(user=self.request.user)

        status_filter = self.request.query_params.get('status')
        if status_filter in Order.Status.values:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve' and is_canteen_staff(self.request.user):
            return StaffOrderDetailSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsStudent()]
        if self.action == 'change_status':
            return [IsCanteenStaff()]
        return super().get_permissions()

    def create(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='status', serializer_class=OrderStatusSerializer)
    def change_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StaffOrderDetailSerializer(order).data)

    @extend_schema(methods=['GET'], tags=[TAG], summary='Чат по заказу', responses=MessageSerializer(many=True),
                   description='Все сообщения по заказу, старые сначала (без страниц). '
                               'Доступно владельцу заказа и сотрудникам.')
    @extend_schema(methods=['POST'], tags=[TAG], summary='Написать в чат', request=MessageSerializer,
                   responses={201: MessageSerializer},
                   description='Владелец заказа или сотрудник. `author_role` в ответе — кто написал.')
    @action(detail=True, methods=['get', 'post'], serializer_class=MessageSerializer, pagination_class=None)
    def messages(self, request, pk=None):
        # get_object() uses get_queryset(), so a student gets 404 for someone else's order.
        order = self.get_object()
        if request.method == 'POST':
            serializer = MessageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(order=order, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        messages = order.messages.select_related('author')
        return Response(MessageSerializer(messages, many=True).data)
