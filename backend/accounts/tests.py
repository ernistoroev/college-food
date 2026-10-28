from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = 'tasty-plov-2026'


class AuthApiTests(APITestCase):
    def register(self, email='aibek@college.kg', name='Айбек', password=PASSWORD):
        return self.client.post('/api/auth/register/', {'name': name, 'email': email, 'password': password})

    def test_register_returns_token_and_user(self):
        response = self.register(email='Aibek@College.kg')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['token'])
        self.assertEqual(response.json()['user']['name'], 'Айбек')
        # The email is stored in lower case and used as the username.
        self.assertEqual(response.json()['user']['email'], 'aibek@college.kg')
        self.assertTrue(User.objects.filter(username='aibek@college.kg').exists())

    def test_register_same_email_twice_fails(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())

    def test_register_weak_password_fails(self):
        response = self.register(password='123')
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        self.register()
        response = self.client.post('/api/auth/login/', {'email': 'aibek@college.kg', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['token'])

    def test_login_wrong_password(self):
        self.register()
        response = self.client.post('/api/auth/login/', {'email': 'aibek@college.kg', 'password': 'wrong'})
        self.assertEqual(response.status_code, 400)

    def test_me_requires_token(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_me_and_profile_update(self):
        token = self.register().json()['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.patch('/api/auth/me/', {'course': '2 курс', 'faculty': 'IT'})
        self.assertEqual(response.status_code, 200)

        me = self.client.get('/api/auth/me/').json()
        self.assertEqual(me['course'], '2 курс')
        self.assertEqual(me['faculty'], 'IT')
        self.assertIsNone(me['avatar'])

    def test_logout_deletes_token(self):
        token = self.register().json()['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 204)
        self.assertFalse(Token.objects.filter(key=token).exists())
