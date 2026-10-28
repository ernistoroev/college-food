from django.db import transaction
from rest_framework import serializers

from accounts.permissions import get_role
from menu.models import Dish

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

    class Meta:
        model = Order
        fields = [
            'id', 'student_name', 'pickup_time', 'comment', 'status', 'status_display',
            'total', 'created_at', 'items',
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

            errors = []
            for dish_id, quantity in quantities.items():
                dish = dishes.get(dish_id)
                if dish is None:
                    errors.append(f'Блюдо №{dish_id} недоступно.')
                elif dish.portions_today < quantity:
                    errors.append(f'«{dish.name}»: осталось только {dish.portions_today} порц.')
            if errors:
                raise serializers.ValidationError({'items': errors})

            # Prices are taken from the database, not from the browser.
            total = sum(dishes[dish_id].price * quantity for dish_id, quantity in quantities.items())
            order = Order.objects.create(
                user=self.context['request'].user,
                student_name=validated_data['student_name'],
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


class OrderStatusSerializer(serializers.Serializer):
    """PATCH /api/orders/{id}/status/ {status} — staff move the order along."""

    status = serializers.ChoiceField(choices=Order.Status.choices)

    def validate(self, data):
        order = self.instance
        if order.status in Order.FINAL_STATUSES:
            raise serializers.ValidationError(
                f'Заказ уже в статусе «{order.get_status_display()}», его нельзя изменить.'
            )
        return data

    def update(self, order, validated_data):
        with transaction.atomic():
            order.status = validated_data['status']
            order.save(update_fields=['status'])
            if order.status == Order.Status.CANCELLED:
                order.return_portions()
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
