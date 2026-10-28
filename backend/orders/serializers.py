from django.db import transaction
from rest_framework import serializers

from menu.models import Dish

from .models import PICKUP_TIMES, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['dish', 'name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """An order as the frontend shows it in «Мои заказы»."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'student_name', 'pickup_time', 'status', 'status_display', 'total', 'created_at', 'items']


class OrderItemInputSerializer(serializers.Serializer):
    dish = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=50)


class OrderCreateSerializer(serializers.Serializer):
    student_name = serializers.CharField(max_length=80)
    pickup_time = serializers.ChoiceField(choices=PICKUP_TIMES)
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
                total=total,
            )
            for dish_id, quantity in quantities.items():
                dish = dishes[dish_id]
                OrderItem.objects.create(order=order, dish=dish, name=dish.name, price=dish.price, quantity=quantity)
                dish.portions_today -= quantity
                dish.save(update_fields=['portions_today'])
        return order
