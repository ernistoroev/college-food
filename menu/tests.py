from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

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
