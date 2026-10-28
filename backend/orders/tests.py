from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.permissions import STAFF_GROUP
from menu.models import Category, Dish

from .models import Message, Order

User = get_user_model()


class OrdersTestCase(APITestCase):
    def setUp(self):
        hot = Category.objects.create(name='Горячее', order=1)
        self.plov = Dish.objects.create(category=hot, name='Плов', price=Decimal('230'), portions_today=5)
        self.manty = Dish.objects.create(category=hot, name='Манты', price=Decimal('180'), portions_today=1)
        self.hidden = Dish.objects.create(
            category=hot, name='Борщ', price=Decimal('150'), portions_today=10, is_available=False
        )
        self.student = User.objects.create_user(
            username='aibek@college.kg', email='aibek@college.kg', password='x', first_name='Айбек'
        )
        self.other = User.objects.create_user(username='aidai@college.kg', password='x', first_name='Айдай')
        self.staff = User.objects.create_user(username='cook@college.kg', password='x', first_name='Повар')
        self.staff.groups.add(Group.objects.get(name=STAFF_GROUP))
        self.client.force_authenticate(self.student)

    def order(self, items, pickup_time='12:20', **extra):
        return self.client.post(
            '/api/orders/',
            {'student_name': 'Айбек', 'pickup_time': pickup_time, 'items': items, **extra},
            format='json',
        )

    def make_order(self, user=None, quantity=1):
        self.client.force_authenticate(user or self.student)
        order_id = self.order([{'dish': self.plov.id, 'quantity': quantity}]).json()['id']
        return Order.objects.get(id=order_id)


class StudentOrdersTests(OrdersTestCase):
    def test_create_order_counts_total_from_db_prices(self):
        response = self.order(
            [{'dish': self.plov.id, 'quantity': 2}, {'dish': self.manty.id, 'quantity': 1}],
            comment='Без лука, пожалуйста',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['total'], 640.0)
        self.assertEqual((data['status'], data['status_display']), ('new', 'Новый'))
        self.assertEqual(data['comment'], 'Без лука, пожалуйста')
        self.assertEqual(data['items'][0]['dish_name'], 'Плов')

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

    def test_unavailable_dish_cannot_be_ordered(self):
        self.assertEqual(self.order([{'dish': self.hidden.id, 'quantity': 1}]).status_code, 400)

    def test_wrong_pickup_time(self):
        self.assertEqual(self.order([{'dish': self.plov.id, 'quantity': 1}], pickup_time='03:00').status_code, 400)

    def test_empty_order(self):
        self.assertEqual(self.order([]).status_code, 400)

    def test_student_sees_only_own_orders(self):
        mine = self.make_order()
        self.make_order(user=self.other)
        self.client.force_authenticate(self.student)
        self.assertEqual([o['id'] for o in self.client.get('/api/orders/').json()['results']], [mine.id])

    def test_student_gets_404_for_someone_elses_order(self):
        others = self.make_order(user=self.other)
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get(f'/api/orders/{others.id}/').status_code, 404)

    def test_student_does_not_get_contacts_and_cannot_change_status(self):
        order = self.make_order()
        detail = self.client.get(f'/api/orders/{order.id}/').json()
        self.assertNotIn('customer_email', detail)
        response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'done'})
        self.assertEqual(response.status_code, 403)

    def test_orders_require_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/orders/').status_code, 401)
        self.assertEqual(self.order([{'dish': self.plov.id, 'quantity': 1}]).status_code, 401)

    def test_staff_cannot_place_orders(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.order([{'dish': self.plov.id, 'quantity': 1}]).status_code, 403)


class StaffOrdersTests(OrdersTestCase):
    def test_staff_sees_all_orders_and_filters_by_status(self):
        first = self.make_order()
        second = self.make_order(user=self.other)
        Order.objects.filter(id=second.id).update(status=Order.Status.COOKING)

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/orders/').json()['count'], 2)
        new_orders = self.client.get('/api/orders/', {'status': 'new'}).json()['results']
        self.assertEqual([o['id'] for o in new_orders], [first.id])

    def test_staff_gets_contacts_only_in_order_detail(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        self.assertNotIn('customer_email', self.client.get('/api/orders/').json()['results'][0])
        detail = self.client.get(f'/api/orders/{order.id}/').json()
        self.assertEqual(detail['customer_name'], 'Айбек')
        self.assertEqual(detail['customer_email'], 'aibek@college.kg')

    def test_staff_moves_order_through_statuses(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        for new_status, display in [('cooking', 'Готовится'), ('ready', 'Готов'), ('done', 'Выдан')]:
            response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': new_status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status_display'], display)

    def test_closed_order_cannot_be_changed(self):
        order = self.make_order()
        Order.objects.filter(id=order.id).update(status=Order.Status.DONE)
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'cooking'})
        self.assertEqual(response.status_code, 400)

    def test_wrong_status(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'eaten'}).status_code, 400)

    def test_cancel_gives_portions_back(self):
        order = self.make_order(quantity=3)
        self.client.force_authenticate(self.staff)
        self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'cancelled'})
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)


class OrderChatTests(OrdersTestCase):
    def test_student_and_staff_chat_about_order(self):
        order = self.make_order()
        response = self.client.post(f'/api/orders/{order.id}/messages/', {'text': 'Можно без лука?'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['author_role'], 'student')

        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/orders/{order.id}/messages/', {'text': 'Да, конечно!'})
        self.assertEqual(response.json()['author_role'], 'staff')
        self.assertEqual(response.json()['author_name'], 'Повар')

        self.client.force_authenticate(self.student)
        chat = self.client.get(f'/api/orders/{order.id}/messages/').json()
        self.assertEqual([m['text'] for m in chat], ['Можно без лука?', 'Да, конечно!'])

    def test_other_student_cannot_read_or_write_chat(self):
        order = self.make_order()
        self.client.post(f'/api/orders/{order.id}/messages/', {'text': 'Секрет'})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/orders/{order.id}/messages/').status_code, 404)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/messages/', {'text': 'Привет'}).status_code, 404)
        self.assertEqual(Message.objects.count(), 1)

    def test_anonymous_cannot_use_chat(self):
        order = self.make_order()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/orders/{order.id}/messages/').status_code, 401)

    def test_empty_message(self):
        order = self.make_order()
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/messages/', {'text': '  '}).status_code, 400)
