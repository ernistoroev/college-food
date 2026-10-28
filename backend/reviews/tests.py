from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Review

User = get_user_model()


class ReviewsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aibek@college.kg', password='x', first_name='Айбек')

    def test_everyone_can_read_reviews(self):
        Review.objects.create(user=self.user, rating=5, text='Очень вкусно!')
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['name'], 'Айбек')
        self.assertEqual(response.json()[0]['rating'], 5)

    def test_only_logged_in_can_write(self):
        response = self.client.post('/api/reviews/', {'rating': 5, 'text': 'Вкусно'})
        self.assertEqual(response.status_code, 401)

    def test_create_review_author_is_current_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/reviews/', {'rating': 4, 'text': '  Хороший плов  '})
        self.assertEqual(response.status_code, 201)
        review = Review.objects.get()
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.text, 'Хороший плов')

    def test_rating_must_be_1_to_5(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 6, 'text': 'x'}).status_code, 400)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 0, 'text': 'x'}).status_code, 400)

    def test_empty_text_is_invalid(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/api/reviews/', {'rating': 5, 'text': '   '}).status_code, 400)
