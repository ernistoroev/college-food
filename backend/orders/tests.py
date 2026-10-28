from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from menu.models import Category, Dish

from .models import Order

User = get_user_model()


class OrdersApiTests(APITestCase):
    def setUp(self):
        hot = Category.objects.create(name='Горячее', order=1)
        self.plov = Dish.objects.create(category=hot, name='Плов', price=Decimal('230'), portions_today=5)
        self.manty = Dish.objects.create(category=hot, name='Манты', price=Decimal('180'), portions_today=1)
        self.hidden = Dish.objects.create(
            category=hot, name='Борщ', price=Decimal('150'), portions_today=10, is_available=False
        )
        self.user = User.objects.create_user(username='aibek@college.kg', password='x', first_name='Айбек')
        self.client.force_authenticate(self.user)

    def order(self, items, pickup_time='12:20'):
        return self.client.post(
            '/api/orders/',
            {'student_name': 'Айбек', 'pickup_time': pickup_time, 'items': items},
            format='json',
        )

    def test_create_order_counts_total_from_db_prices(self):
        response = self.order([{'dish': self.plov.id, 'quantity': 2}, {'dish': self.manty.id, 'quantity': 1}])
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['total'], 640.0)
        self.assertEqual(data['status_display'], 'Принят')
        self.assertEqual(len(data['items']), 2)

    def test_order_takes_portions(self):
        self.order([{'dish': self.plov.id, 'quantity': 2}])
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 3)

    def test_same_dish_twice_is_added_up(self):
        response = self.order([{'dish': self.plov.id, 'quantity': 1}, {'dish': self.plov.id, 'quantity': 2}])
        self.assertEqual(response.json()['items'][0]['quantity'], 3)

    def test_not_enough_portions(self):
        response = self.order([{'dish': self.plov.id, 'quantity': 1}, {'dish': self.manty.id, 'quantity': 2}])
        self.assertEqual(response.status_code, 400)
        # Nothing is taken if the order fails.
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)
        self.assertEqual(Order.objects.count(), 0)

    def test_hidden_dish_cannot_be_ordered(self):
        response = self.order([{'dish': self.hidden.id, 'quantity': 1}])
        self.assertEqual(response.status_code, 400)

    def test_wrong_pickup_time(self):
        response = self.order([{'dish': self.plov.id, 'quantity': 1}], pickup_time='03:00')
        self.assertEqual(response.status_code, 400)

    def test_empty_order(self):
        self.assertEqual(self.order([]).status_code, 400)

    def test_user_sees_only_own_orders(self):
        self.order([{'dish': self.plov.id, 'quantity': 1}])
        other = User.objects.create_user(username='other@college.kg', password='x')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get('/api/orders/').json(), [])

    def test_orders_require_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/orders/').status_code, 401)
        self.assertEqual(self.order([{'dish': self.plov.id, 'quantity': 1}]).status_code, 401)
