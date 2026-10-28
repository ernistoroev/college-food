from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.permissions import STAFF_GROUP
from menu.models import Category, Dish
from orders.models import Order
from reviews.models import Review

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self):
        hot = Category.objects.create(name='Горячее', order=1)
        plov = Dish.objects.create(category=hot, name='Плов', price=Decimal('230'), portions_today=5)
        Dish.objects.create(category=hot, name='Манты', price=Decimal('180'), portions_today=0)
        Dish.objects.create(category=hot, name='Борщ', price=Decimal('150'), is_available=False)

        self.student = User.objects.create_user(username='aibek@college.kg', password='x', first_name='Айбек')
        self.staff = User.objects.create_user(username='cook@college.kg', password='x')
        self.staff.groups.add(Group.objects.get(name=STAFF_GROUP))

        for status in ['new', 'new', 'cooking', 'done']:
            Order.objects.create(user=self.student, student_name='Айбек', pickup_time='12:20',
                                 total=Decimal('230'), status=status)
        for number in range(7):
            Review.objects.create(user=self.student, rating=5, text=f'Отзыв {number}', is_visible=number != 6)
        Review.objects.create(user=self.student, dish=plov, rating=4, text='Последний о плове')

    def test_staff_gets_numbers(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['dishes_total'], 3)
        self.assertEqual(data['dishes_unavailable'], 1)
        self.assertEqual(data['dishes_sold_out'], 1)
        self.assertEqual((data['orders_new'], data['orders_cooking'], data['orders_ready']), (2, 1, 0))

    def test_latest_reviews_newest_first_including_hidden(self):
        self.client.force_authenticate(self.staff)
        reviews = self.client.get('/api/staff/dashboard/').json()['latest_reviews']
        self.assertEqual(len(reviews), 5)
        self.assertEqual(reviews[0]['text'], 'Последний о плове')
        self.assertEqual(reviews[0]['dish_name'], 'Плов')
        self.assertEqual(reviews[0]['user_name'], 'Айбек')
        self.assertFalse(reviews[1]['is_visible'])

    def test_student_gets_403(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 403)

    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 401)
