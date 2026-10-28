from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError
from django.test import TestCase
from PIL import Image
from rest_framework.test import APITestCase

from accounts.permissions import STAFF_GROUP

from .models import Category, Dish

User = get_user_model()


class MenuModelsTests(TestCase):
    def setUp(self):
        self.drinks = Category.objects.create(name='Напитки', order=2)
        self.hot = Category.objects.create(name='Горячее', order=1)

    def test_str(self):
        dish = Dish.objects.create(category=self.hot, name='Плов', price=Decimal('180'))
        self.assertEqual(str(self.hot), 'Горячее')
        self.assertEqual(str(dish), 'Плов')

    def test_dish_defaults(self):
        dish = Dish.objects.create(category=self.hot, name='Лагман', price=Decimal('170'))
        self.assertTrue(dish.is_available)
        self.assertFalse(dish.image)

    def test_categories_ordered_by_order(self):
        self.assertEqual(list(Category.objects.all()), [self.hot, self.drinks])

    def test_dishes_ordered_by_category_then_name(self):
        tea = Dish.objects.create(category=self.drinks, name='Чай', price=Decimal('25'))
        plov = Dish.objects.create(category=self.hot, name='Плов', price=Decimal('180'))
        lagman = Dish.objects.create(category=self.hot, name='Лагман', price=Decimal('170'))
        self.assertEqual(list(Dish.objects.all()), [lagman, plov, tea])

    def test_negative_price_is_invalid(self):
        dish = Dish(category=self.hot, name='Плов', price=Decimal('-1'))
        with self.assertRaises(ValidationError):
            dish.full_clean()

    def test_category_with_dishes_cannot_be_deleted(self):
        Dish.objects.create(category=self.hot, name='Плов', price=Decimal('180'))
        with self.assertRaises(ProtectedError):
            self.hot.delete()


    def test_search_name_is_lower_case_name(self):
        dish = Dish.objects.create(category=self.hot, name='Плов ПО-Восточному', price=Decimal('180'))
        self.assertEqual(dish.search_name, 'плов по-восточному')
        dish.name = 'Лагман'
        dish.save(update_fields=['name'])
        dish.refresh_from_db()
        self.assertEqual(dish.search_name, 'лагман')


def make_staff(username='cook@college.kg'):
    user = User.objects.create_user(username=username, password='x')
    user.groups.add(Group.objects.get(name=STAFF_GROUP))
    return user


class MenuApiTests(APITestCase):
    def setUp(self):
        self.hot = Category.objects.create(name='Горячее', order=1)
        self.drinks = Category.objects.create(name='Напитки', order=2)
        self.plov = Dish.objects.create(category=self.hot, name='Плов', price=Decimal('180'))
        self.tea = Dish.objects.create(category=self.drinks, name='Чай', price=Decimal('25'))
        self.hidden = Dish.objects.create(
            category=self.hot, name='Манты', price=Decimal('150'), is_available=False
        )

    def test_categories_list(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'],
            [{'id': self.hot.id, 'name': 'Горячее', 'order': 1},
             {'id': self.drinks.id, 'name': 'Напитки', 'order': 2}],
        )

    def test_unavailable_dishes_are_listed_with_flag(self):
        response = self.client.get('/api/dishes/')
        self.assertEqual(response.status_code, 200)
        dishes = {d['name']: d['is_available'] for d in response.json()['results']}
        self.assertEqual(dishes, {'Манты': False, 'Плов': True, 'Чай': True})
        self.assertEqual(self.client.get(f'/api/dishes/{self.hidden.id}/').status_code, 200)

    def test_dish_fields(self):
        dish = self.client.get(f'/api/dishes/{self.plov.id}/').json()
        self.assertEqual(dish, {
            'id': self.plov.id,
            'name': 'Плов',
            'description': '',
            'price': 180.0,
            'weight': 0,
            'weight_unit': 'г',
            'portions_today': 0,
            'is_available': True,
            'image': None,
            'category': self.hot.id,
            'category_name': 'Горячее',
            'rating': None,
            'reviews_count': 0,
        })

    def test_dish_weight_and_portions_today(self):
        self.plov.weight = 350
        self.plov.portions_today = 20
        self.plov.save()

        response = self.client.get(f'/api/dishes/{self.plov.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['weight'], 350)
        self.assertEqual(response.json()['portions_today'], 20)


    def names(self, **params):
        return [d['name'] for d in self.client.get('/api/dishes/', params).json()['results']]

    def test_filter_by_category(self):
        self.assertEqual(self.names(category=self.drinks.id), ['Чай'])

    def test_search_ignores_case_in_cyrillic(self):
        for term in ['плов', 'ПЛОВ', 'Пл']:
            self.assertEqual(self.names(search=term), ['Плов'], term)
        self.assertEqual(self.names(search='борщ'), [])

    def test_filter_by_availability(self):
        self.assertEqual(self.names(available='false'), ['Манты'])
        self.assertEqual(self.names(available='true'), ['Плов', 'Чай'])
        # Any other value is ignored, the whole menu comes back.
        self.assertEqual(len(self.names(available='maybe')), 3)

    def test_pagination(self):
        for number in range(25):
            Dish.objects.create(category=self.hot, name=f'Блюдо {number:02}', price=Decimal('10'))
        first = self.client.get('/api/dishes/').json()
        self.assertEqual(first['count'], 28)
        self.assertEqual(len(first['results']), 20)
        self.assertIsNotNone(first['next'])
        second = self.client.get('/api/dishes/', {'page': 2}).json()
        self.assertEqual(len(second['results']), 8)
        # The whole menu in one request.
        self.assertEqual(len(self.client.get('/api/dishes/', {'page_size': 100}).json()['results']), 28)


class MenuPermissionsTests(APITestCase):
    """Who can change the menu: anonymous — only read, student — 403, staff — everything."""

    def setUp(self):
        self.hot = Category.objects.create(name='Горячее', order=1)
        self.plov = Dish.objects.create(category=self.hot, name='Плов', price=Decimal('180'))
        self.student = User.objects.create_user(username='student@college.kg', password='x')
        self.staff = make_staff()
        self.new_dish = {'name': 'Борщ', 'price': '150', 'category': self.hot.id}

    def write_requests(self):
        return [
            self.client.post('/api/dishes/', self.new_dish),
            self.client.patch(f'/api/dishes/{self.plov.id}/', {'price': '1'}),
            self.client.patch(f'/api/dishes/{self.plov.id}/availability/', {'is_available': False}),
            self.client.delete(f'/api/dishes/{self.plov.id}/'),
            self.client.post('/api/categories/', {'name': 'Супы'}),
            self.client.delete(f'/api/categories/{self.hot.id}/'),
        ]

    def test_anonymous_can_only_read(self):
        self.assertEqual(self.client.get('/api/dishes/').status_code, 200)
        self.assertEqual(self.client.get('/api/categories/').status_code, 200)
        for response in self.write_requests():
            self.assertEqual(response.status_code, 401)

    def test_student_gets_403_on_menu_changes(self):
        self.client.force_authenticate(self.student)
        for response in self.write_requests():
            self.assertEqual(response.status_code, 403)
        self.plov.refresh_from_db()
        self.assertEqual(self.plov.price, Decimal('180'))

    def test_staff_creates_dish(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/dishes/', self.new_dish)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['category_name'], 'Горячее')
        self.assertTrue(Dish.objects.filter(name='Борщ').exists())

    def test_staff_updates_and_deletes_dish(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/dishes/{self.plov.id}/', {'price': '200'})
        self.assertEqual(response.json()['price'], 200.0)
        self.assertEqual(self.client.delete(f'/api/dishes/{self.plov.id}/').status_code, 204)
        self.assertFalse(Dish.objects.filter(id=self.plov.id).exists())

    def test_staff_toggles_availability(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/dishes/{self.plov.id}/availability/', {'is_available': False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_available'])
        self.plov.refresh_from_db()
        self.assertFalse(self.plov.is_available)

    def test_availability_needs_value(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/dishes/{self.plov.id}/availability/', {})
        self.assertEqual(response.status_code, 400)

    def test_staff_uploads_photo(self):
        self.client.force_authenticate(self.staff)
        photo = BytesIO()
        Image.new('RGB', (10, 10), 'orange').save(photo, 'JPEG')
        upload = SimpleUploadedFile('plov.jpg', photo.getvalue(), content_type='image/jpeg')

        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.patch(f'/api/dishes/{self.plov.id}/', {'image': upload}, format='multipart')
            self.assertEqual(response.status_code, 200)
            self.assertIn('/media/dishes/', response.json()['image'])

    def test_staff_manages_categories(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/categories/', {'name': 'Супы', 'order': 2})
        self.assertEqual(response.status_code, 201)
        soups = response.json()['id']
        self.assertEqual(self.client.patch(f'/api/categories/{soups}/', {'order': 5}).status_code, 200)
        self.assertEqual(self.client.delete(f'/api/categories/{soups}/').status_code, 204)

    def test_category_with_dishes_is_not_deleted(self):
        self.client.force_authenticate(self.staff)
        response = self.client.delete(f'/api/categories/{self.hot.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Category.objects.filter(id=self.hot.id).exists())
