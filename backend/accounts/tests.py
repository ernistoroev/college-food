from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from .permissions import STAFF_GROUP, get_role, is_canteen_staff

User = get_user_model()

PASSWORD = 'tasty-plov-2026'


class AuthApiTests(APITestCase):
    def register(self, email='aibek@college.kg', name='Айбек', password=PASSWORD):
        return self.client.post('/api/auth/register/', {'name': name, 'email': email, 'password': password})

    def login(self, email='aibek@college.kg', password=PASSWORD):
        return self.client.post('/api/auth/login/', {'email': email, 'password': password})

    def test_register_returns_jwt_and_student_role(self):
        response = self.register(email='Aibek@College.kg')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['access'])
        self.assertTrue(data['refresh'])
        self.assertEqual(data['user']['role'], 'student')
        self.assertEqual(data['user']['name'], 'Айбек')
        # The email is stored in lower case and used as the login.
        self.assertEqual(data['user']['email'], 'aibek@college.kg')

    def test_register_same_email_twice_fails(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())

    def test_register_weak_password_fails(self):
        self.assertEqual(self.register(password='123').status_code, 400)

    def test_login_returns_role(self):
        self.register()
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['role'], 'student')

    def test_staff_login_returns_staff_role(self):
        staff = User.objects.create_user(username='cook@college.kg', email='cook@college.kg', password=PASSWORD)
        staff.groups.add(Group.objects.get(name=STAFF_GROUP))
        response = self.login(email='cook@college.kg')
        self.assertEqual(response.json()['user']['role'], 'staff')

    def test_login_wrong_password(self):
        self.register()
        self.assertEqual(self.login(password='wrong').status_code, 400)

    def test_refresh_gives_new_access_token(self):
        refresh = self.register().json()['refresh']
        response = self.client.post('/api/auth/refresh/', {'refresh': refresh})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['access'])

    def test_refresh_with_bad_token(self):
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': 'bad'}).status_code, 401)

    def test_me_requires_token(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_me_with_access_token_and_profile_update(self):
        access = self.register().json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        response = self.client.patch('/api/auth/me/', {'course': '2 курс', 'faculty': 'IT'})
        self.assertEqual(response.status_code, 200)

        me = self.client.get('/api/auth/me/').json()
        self.assertEqual(me['role'], 'student')
        self.assertEqual(me['course'], '2 курс')
        self.assertEqual(me['faculty'], 'IT')
        self.assertIsNone(me['avatar'])

    def test_bad_access_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-token')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)


class RolesTests(APITestCase):
    def test_staff_group_is_created_by_migration(self):
        self.assertTrue(Group.objects.filter(name=STAFF_GROUP).exists())

    def test_roles(self):
        student = User.objects.create_user(username='student@college.kg', password=PASSWORD)
        cook = User.objects.create_user(username='cook@college.kg', password=PASSWORD)
        cook.groups.add(Group.objects.get(name=STAFF_GROUP))
        owner = User.objects.create_superuser(username='owner@college.kg', password=PASSWORD)
        # is_staff only opens the Django admin; it does not make someone canteen staff.
        admin_only = User.objects.create_user(username='admin@college.kg', password=PASSWORD, is_staff=True)

        self.assertEqual(get_role(student), 'student')
        self.assertEqual(get_role(cook), 'staff')
        self.assertEqual(get_role(owner), 'staff')
        self.assertEqual(get_role(admin_only), 'student')
        self.assertFalse(is_canteen_staff(None))
