from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.permissions import STAFF_GROUP
from menu.models import Canteen, Category, Dish

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
        # The canteens are created by the menu migration: 1st, 5th and 6th floor.
        self.first, self.fifth, self.sixth = Canteen.objects.order_by('floor')
        for dish in (self.plov, self.manty, self.hidden):
            dish.canteens.set([self.first, self.fifth, self.sixth])
        self.spaghetti = Dish.objects.create(category=hot, name='Спагетти', price=Decimal('200'), portions_today=5)
        self.spaghetti.canteens.set([self.first])
        self.student = User.objects.create_user(
            username='aibek@college.kg', email='aibek@college.kg', password='x', first_name='Айбек'
        )
        self.other = User.objects.create_user(username='aidai@college.kg', password='x', first_name='Айдай')
        self.staff = User.objects.create_user(username='cook@college.kg', password='x', first_name='Повар')
        self.staff.groups.add(Group.objects.get(name=STAFF_GROUP))
        self.client.force_authenticate(self.student)

    def order(self, items, pickup_time='12:20', **extra):
        data = {'student_name': 'Айбек', 'canteen': self.fifth.id, 'pickup_time': pickup_time, 'items': items, **extra}
        return self.client.post('/api/orders/', {k: v for k, v in data.items() if v is not None}, format='json')

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

    def test_order_remembers_canteen(self):
        data = self.order([{'dish': self.plov.id, 'quantity': 1}], canteen=self.sixth.id).json()
        self.assertEqual((data['canteen'], data['canteen_name']), (self.sixth.id, '6 этаж'))

    def test_canteen_is_required_and_checked(self):
        for canteen in [None, 999, '']:
            with self.subTest(canteen=canteen):
                self.assertEqual(self.order([{'dish': self.plov.id, 'quantity': 1}], canteen=canteen).status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_dish_only_in_its_canteens(self):
        # Spaghetti is served only on the 1st floor: it cannot be collected on the 5th.
        items = [{'dish': self.plov.id, 'quantity': 1}, {'dish': self.spaghetti.id, 'quantity': 1}]
        response = self.order(items)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['items'], ['«Спагетти» не доставляют на 5 этаж.'])
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)

        self.assertEqual(self.order(items, canteen=self.first.id).status_code, 201)

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

    def test_staff_filters_orders_by_canteen(self):
        first = self.make_order()
        second = self.make_order(user=self.other)
        Order.objects.filter(id=second.id).update(canteen=self.first)

        self.client.force_authenticate(self.staff)
        fifth_floor = self.client.get('/api/orders/', {'canteen': self.fifth.id}).json()['results']
        self.assertEqual([o['id'] for o in fifth_floor], [first.id])
        both = self.client.get('/api/orders/', {'canteen': self.first.id, 'status': 'new'}).json()['results']
        self.assertEqual([o['id'] for o in both], [second.id])

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


class OrderWorkflowTests(OrdersTestCase):
    """Status order, accepting and rejecting orders, status messages in the chat."""

    def chat_texts(self, order):
        return list(order.messages.values_list('text', flat=True))

    def test_status_cannot_skip_steps_or_go_back(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'done'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('«Готовится», «Отменён»', response.json()['status'][0])

        Order.objects.filter(id=order.id).update(status=Order.Status.READY)
        self.assertEqual(self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'new'}).status_code, 400)
        self.assertEqual(self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'ready'}).status_code, 400)

    def test_status_change_writes_to_chat(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'cooking'})
        self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'ready'})

        self.client.force_authenticate(self.student)
        chat = self.client.get(f'/api/orders/{order.id}/messages/').json()
        self.assertEqual([m['text'] for m in chat], ['Статус заказа: Готовится.', 'Статус заказа: Готов.'])
        self.assertEqual(chat[0]['author_role'], 'staff')

    def test_staff_accepts_new_order(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/orders/{order.id}/accept/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'cooking')
        self.assertEqual(self.chat_texts(order), ['Статус заказа: Готовится.'])
        # Only a new order can be accepted.
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/accept/').status_code, 400)

    def test_staff_rejects_order_with_reason(self):
        order = self.make_order(quantity=3)
        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/orders/{order.id}/reject/', {'reason': 'Плов закончился'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'cancelled')
        self.assertEqual(self.chat_texts(order), ['Статус заказа: Отменён. Причина: Плов закончился'])
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)
        # A cancelled order cannot be rejected again, and the portions are not given back twice.
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/reject/', {'reason': 'Ещё раз'}).status_code, 400)
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)

    def test_reject_needs_reason(self):
        order = self.make_order()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/reject/', {'reason': ' '}).status_code, 400)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/reject/').status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.NEW)

    def test_student_cannot_accept_or_reject(self):
        order = self.make_order()
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/accept/').status_code, 403)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/reject/', {'reason': 'нет'}).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/accept/').status_code, 401)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.NEW)

    def test_admin_status_change_writes_to_chat_and_returns_portions(self):
        order = self.make_order(quantity=2)
        self.staff.is_staff = self.staff.is_superuser = True
        self.staff.save()
        self.client.force_login(self.staff)
        response = self.client.post(f'/admin/orders/order/{order.id}/change/', {
            'status': 'cancelled',
            'items-TOTAL_FORMS': 1, 'items-INITIAL_FORMS': 1, 'items-0-id': order.items.get().id,
            'items-0-order': order.id,
            'messages-TOTAL_FORMS': 0, 'messages-INITIAL_FORMS': 0,
        })
        self.assertEqual(response.status_code, 302)
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.portions_today, 5)
        self.assertEqual(self.chat_texts(order), ['Статус заказа: Отменён.'])


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
