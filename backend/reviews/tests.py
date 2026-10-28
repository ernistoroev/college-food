from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from rest_framework.test import APITestCase

from accounts.permissions import STAFF_GROUP
from menu.models import Category, Dish

from .models import Review

User = get_user_model()


class ReviewsTestCase(APITestCase):
    def setUp(self):
        hot = Category.objects.create(name='Горячее', order=1)
        self.plov = Dish.objects.create(category=hot, name='Плов', price=Decimal('230'))
        self.manty = Dish.objects.create(category=hot, name='Манты', price=Decimal('180'))
        self.student = User.objects.create_user(username='aibek@college.kg', password='x', first_name='Айбек')
        self.other = User.objects.create_user(username='aidai@college.kg', password='x', first_name='Айдай')
        self.staff = User.objects.create_user(username='cook@college.kg', password='x')
        self.staff.groups.add(Group.objects.get(name=STAFF_GROUP))


class ReviewsApiTests(ReviewsTestCase):
    def test_everyone_can_read_visible_reviews(self):
        Review.objects.create(user=self.student, rating=5, text='Очень вкусно!')
        Review.objects.create(user=self.other, rating=1, text='Спам', is_visible=False)
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual([r['text'] for r in results], ['Очень вкусно!'])
        self.assertEqual(results[0]['user_name'], 'Айбек')

    def test_anonymous_cannot_write(self):
        response = self.client.post('/api/reviews/', {'rating': 5, 'text': 'Вкусно'})
        self.assertEqual(response.status_code, 401)

    def test_staff_cannot_write_reviews(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/reviews/', {'rating': 5, 'text': 'Сам себя хвалю'})
        self.assertEqual(response.status_code, 403)

    def test_student_reviews_canteen_and_dish(self):
        self.client.force_authenticate(self.student)
        canteen = self.client.post('/api/reviews/', {'rating': 4, 'text': '  Уютно  '})
        self.assertEqual(canteen.status_code, 201)
        self.assertIsNone(canteen.json()['dish'])
        self.assertEqual(Review.objects.get(dish=None).text, 'Уютно')

        dish = self.client.post('/api/reviews/', {'rating': 5, 'text': 'Лучший плов', 'dish': self.plov.id})
        self.assertEqual(dish.status_code, 201)
        self.assertEqual(dish.json()['dish_name'], 'Плов')
        # The author is the current user, whatever the browser sends.
        self.assertEqual(Review.objects.get(dish=self.plov).user, self.student)

    def test_one_review_per_dish(self):
        self.client.force_authenticate(self.student)
        self.client.post('/api/reviews/', {'rating': 5, 'text': 'Вкусно', 'dish': self.plov.id})
        again = self.client.post('/api/reviews/', {'rating': 1, 'text': 'Ещё раз', 'dish': self.plov.id})
        self.assertEqual(again.status_code, 400)
        self.assertIn('dish', again.json())
        # Another dish and the canteen in general are still allowed.
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 4, 'text': 'Тоже', 'dish': self.manty.id}).status_code, 201)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 4, 'text': 'Раз'}).status_code, 201)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 4, 'text': 'Два'}).status_code, 201)

    def test_database_also_forbids_second_review_of_dish(self):
        Review.objects.create(user=self.student, dish=self.plov, rating=5, text='a')
        with self.assertRaises(IntegrityError):
            Review.objects.create(user=self.student, dish=self.plov, rating=4, text='b')

    def test_rating_must_be_1_to_5(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 6, 'text': 'x'}).status_code, 400)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 0, 'text': 'x'}).status_code, 400)

    def test_empty_text_is_invalid(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 5, 'text': '   '}).status_code, 400)

    def test_filter_by_dish(self):
        Review.objects.create(user=self.student, dish=self.plov, rating=5, text='о плове')
        Review.objects.create(user=self.student, rating=4, text='о столовой')
        by_dish = self.client.get('/api/reviews/', {'dish': self.plov.id}).json()['results']
        self.assertEqual([r['text'] for r in by_dish], ['о плове'])
        canteen = self.client.get('/api/reviews/', {'dish': 'none'}).json()['results']
        self.assertEqual([r['text'] for r in canteen], ['о столовой'])


class ModerationTests(ReviewsTestCase):
    def setUp(self):
        super().setUp()
        self.review = Review.objects.create(user=self.student, dish=self.plov, rating=1, text='Грубость')

    def test_staff_hides_and_shows_review(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f'/api/reviews/{self.review.id}/', {'is_visible': False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_visible'])

        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/reviews/').json()['results'], [])
        self.assertEqual(self.client.get(f'/api/reviews/{self.review.id}/').status_code, 404)

    def test_staff_sees_hidden_reviews(self):
        self.review.is_visible = False
        self.review.save()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/reviews/').json()['count'], 1)

    def test_staff_can_change_only_visibility(self):
        self.client.force_authenticate(self.staff)
        self.client.patch(f'/api/reviews/{self.review.id}/', {'is_visible': False, 'text': 'Подделка', 'rating': 5})
        self.review.refresh_from_db()
        self.assertEqual((self.review.text, self.review.rating), ('Грубость', 1))

    def test_moderation_needs_value(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.patch(f'/api/reviews/{self.review.id}/', {}).status_code, 400)

    def test_staff_deletes_review(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(f'/api/reviews/{self.review.id}/').status_code, 204)
        self.assertFalse(Review.objects.exists())

    def test_student_cannot_moderate(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.patch(f'/api/reviews/{self.review.id}/', {'is_visible': False}).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/reviews/{self.review.id}/').status_code, 403)
        self.assertTrue(Review.objects.get().is_visible)

    def test_anonymous_cannot_moderate(self):
        self.assertEqual(self.client.delete(f'/api/reviews/{self.review.id}/').status_code, 401)


class DishRatingTests(ReviewsTestCase):
    def test_dish_card_has_rating_of_visible_reviews_only(self):
        Review.objects.create(user=self.student, dish=self.plov, rating=5, text='a')
        Review.objects.create(user=self.other, dish=self.plov, rating=4, text='b')
        Review.objects.create(user=self.staff, dish=self.plov, rating=1, text='скрыт', is_visible=False)

        dish = self.client.get(f'/api/dishes/{self.plov.id}/').json()
        self.assertEqual(dish['rating'], 4.5)
        self.assertEqual(dish['reviews_count'], 2)

        manty = self.client.get(f'/api/dishes/{self.manty.id}/').json()
        self.assertEqual((manty['rating'], manty['reviews_count']), (None, 0))

    def test_dish_reviews_endpoint_shows_only_visible(self):
        Review.objects.create(user=self.student, dish=self.plov, rating=5, text='видимый')
        Review.objects.create(user=self.other, dish=self.plov, rating=1, text='скрытый', is_visible=False)
        Review.objects.create(user=self.student, dish=self.manty, rating=3, text='о мантах')
        response = self.client.get(f'/api/dishes/{self.plov.id}/reviews/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['text'] for r in response.json()['results']], ['видимый'])
