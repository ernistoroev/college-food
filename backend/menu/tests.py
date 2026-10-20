from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Category, Dish


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
            response.json(),
            [{'id': self.hot.id, 'name': 'Горячее'}, {'id': self.drinks.id, 'name': 'Напитки'}],
        )

    def test_dishes_list_shows_only_available(self):
        response = self.client.get('/api/dishes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([d['name'] for d in response.json()], ['Плов', 'Чай'])

    def test_dish_fields(self):
        dish = self.client.get(f'/api/dishes/{self.plov.id}/').json()
        self.assertEqual(dish, {
            'id': self.plov.id,
            'name': 'Плов',
            'description': '',
            'price': 180.0,
            'image': None,
            'category': self.hot.id,
            'category_name': 'Горячее',
        })

    def test_hidden_dish_detail_not_found(self):
        response = self.client.get(f'/api/dishes/{self.hidden.id}/')
        self.assertEqual(response.status_code, 404)

    def test_filter_by_category(self):
        response = self.client.get('/api/dishes/', {'category': self.drinks.id})
        self.assertEqual([d['name'] for d in response.json()], ['Чай'])

    def test_api_is_read_only(self):
        response = self.client.post('/api/dishes/', {'name': 'Борщ'})
        self.assertEqual(response.status_code, 405)
