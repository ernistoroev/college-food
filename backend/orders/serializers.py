from django.db import transaction
from rest_framework import serializers

from accounts.permissions import get_role
from menu.models import Canteen, Dish

from .models import PICKUP_TIMES, Message, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    # The name and price are copies made at the moment of the order.
    dish_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['dish', 'dish_name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """An order in lists: for the student in «Мои заказы» and for staff in the order list."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    canteen_name = serializers.CharField(source='canteen.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'student_name', 'canteen', 'canteen_name', 'pickup_time', 'comment', 'status',
            'status_display', 'total', 'created_at', 'items',
        ]


class StaffOrderDetailSerializer(OrderSerializer):
    """One order for staff: the only place where they get the student's contacts."""

    customer_name = serializers.CharField(source='user.first_name', read_only=True)
    customer_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = [*OrderSerializer.Meta.fields, 'customer_name', 'customer_email']


class OrderItemInputSerializer(serializers.Serializer):
    dish = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=50)


class OrderCreateSerializer(serializers.Serializer):
    student_name = serializers.CharField(max_length=80)
    canteen = serializers.PrimaryKeyRelatedField(queryset=Canteen.objects.all(), help_text='id столовой из /api/canteens/.')
    pickup_time = serializers.ChoiceField(choices=PICKUP_TIMES)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_student_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажи имя.')
        return value

    def create(self, validated_data):
        # The same dish may come twice — add the quantities up.
        quantities = {}
        for item in validated_data['items']:
            quantities[item['dish']] = quantities.get(item['dish'], 0) + item['quantity']

        # atomic + select_for_update: two students cannot take the last portion at the same time,
        # and if anything fails, no portions are taken at all.
        with transaction.atomic():
            dishes = Dish.objects.select_for_update().filter(id__in=quantities, is_available=True)
            dishes = {dish.id: dish for dish in dishes}
            canteen = validated_data['canteen']
            served_here = set(canteen.dishes.filter(id__in=quantities).values_list('id', flat=True))

            errors = []
            for dish_id, quantity in quantities.items():
                dish = dishes.get(dish_id)
                if dish is None:
                    errors.append(f'Блюдо №{dish_id} недоступно.')
                elif dish_id not in served_here:
                    errors.append(f'«{dish.name}» нет в столовой на {canteen.floor} этаже.')
                elif dish.portions_today < quantity:
                    errors.append(f'«{dish.name}»: осталось только {dish.portions_today} порц.')
            if errors:
                raise serializers.ValidationError({'items': errors})

            # Prices are taken from the database, not from the browser.
            total = sum(dishes[dish_id].price * quantity for dish_id, quantity in quantities.items())
            order = Order.objects.create(
                user=self.context['request'].user,
                student_name=validated_data['student_name'],
                canteen=validated_data['canteen'],
                pickup_time=validated_data['pickup_time'],
                comment=validated_data.get('comment', '').strip(),
                total=total,
            )
            for dish_id, quantity in quantities.items():
                dish = dishes[dish_id]
                OrderItem.objects.create(order=order, dish=dish, name=dish.name, price=dish.price, quantity=quantity)
                dish.portions_today -= quantity
                dish.save(update_fields=['portions_today'])
        return order


def check_order_is_open(order):
    if order.status in Order.FINAL_STATUSES:
        raise serializers.ValidationError(
            f'Заказ уже в статусе «{order.get_status_display()}», его нельзя изменить.'
        )


class OrderStatusSerializer(serializers.Serializer):
    """PATCH /api/orders/{id}/status/ {status, reason?} — staff move the order one step along or cancel it."""

    status = serializers.ChoiceField(choices=Order.Status.choices)
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate(self, data):
        order = self.instance
        check_order_is_open(order)
        allowed = Order.NEXT_STATUSES[order.status]
        if data['status'] not in allowed:
            names = ', '.join(f'«{Order.Status(status).label}»' for status in allowed)
            raise serializers.ValidationError(
                {'status': f'Из статуса «{order.get_status_display()}» можно перевести только в: {names}.'}
            )
        return data

    def update(self, order, validated_data):
        order.set_status(
            validated_data['status'], by=self.context['request'].user, reason=validated_data.get('reason', '').strip()
        )
        return order


class OrderRejectSerializer(serializers.Serializer):
    """POST /api/orders/{id}/reject/ {reason} — staff turn the order down; the student sees the reason in the chat."""

    reason = serializers.CharField(max_length=300)

    def validate_reason(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Напиши причину, её увидит студент.')
        return value

    def validate(self, data):
        check_order_is_open(self.instance)
        return data

    def update(self, order, validated_data):
        order.set_status(Order.Status.CANCELLED, by=self.context['request'].user, reason=validated_data['reason'])
        return order


class MessageSerializer(serializers.ModelSerializer):
    """A chat message; author_role tells the chat which side to draw the message on."""

    author_name = serializers.CharField(source='author.first_name', read_only=True)
    author_role = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'order', 'author', 'author_name', 'author_role', 'text', 'created_at']
        read_only_fields = ['id', 'order', 'author', 'author_name', 'author_role', 'created_at']

    def get_author_role(self, message) -> str:
        return get_role(message.author)

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Напиши сообщение.')
        return value
