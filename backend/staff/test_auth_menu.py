from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from accounts.permissions import STAFF_GROUP
from menu.models import Category, Dish

User = get_user_model()


class StaffAccessTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student@college.kg', password='strong-password')
        self.staff = User.objects.create_user(username='staff@college.kg', password='strong-password')
        self.staff.groups.add(Group.objects.get(name=STAFF_GROUP))
        self.category = Category.objects.create(name='Супы')
        self.dish = Dish.objects.create(name='Суп', category=self.category, price=100, portions_today=5)

    def login(self, user, staff=True, password='strong-password'):
        return self.client.post('/api/staff/auth/login/' if staff else '/api/auth/login/', {'email':user.username, 'password':password})

    def test_staff_login_issues_working_jwt(self):
        response = self.login(self.staff)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['user']['role'],'staff')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.data['access'])
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code,200)
        self.assertEqual(self.client.patch(f'/api/dishes/{self.dish.id}/',{'portions_today':8}).status_code,200)

    def test_student_staff_login_rejected(self):
        response=self.login(self.student)
        self.assertEqual(response.status_code,403)
        self.assertNotIn('access',response.data)

    def test_wrong_password_and_inactive_staff_rejected(self):
        self.assertEqual(self.login(self.staff,password='wrong').status_code,400)
        self.staff.is_active=False
        self.staff.save()
        self.assertEqual(self.login(self.staff).status_code,400)

    def test_registration_cannot_assign_role(self):
        response=self.client.post('/api/auth/register/',{'name':'Student','email':'new@college.kg','password':'Strong-Unusual-321!','role':'staff','is_staff':True,'is_superuser':True})
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data['user']['role'],'student')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.data['access'])
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code,403)

    def test_student_jwt_blocks_all_menu_writes(self):
        response=self.login(self.student,staff=False)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.data['access'])
        url=f'/api/dishes/{self.dish.id}/'
        for method,path,data in [('post','/api/dishes/',{'name':'X','price':1,'category':self.category.id}),('put',url,{'name':'X','price':1,'category':self.category.id}),('patch',url,{'portions_today':999}),('patch',url+'availability/',{'is_available':False}),('delete',url,{})]:
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client,method)(path,data,format='json').status_code,403)
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.portions_today,5)

    def test_staff_flag_alone_not_sufficient(self):
        self.student.is_staff=True
        self.student.save()
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.patch(f'/api/dishes/{self.dish.id}/',{'portions_today':99}).status_code,403)

    def test_portions_and_photo_validation(self):
        self.client.force_authenticate(self.staff)
        url=f'/api/dishes/{self.dish.id}/'
        self.assertEqual(self.client.patch(url,{'portions_today':0}).status_code,200)
        self.assertEqual(self.client.patch(url,{'portions_today':-1}).status_code,400)
        upload=SimpleUploadedFile('fake.jpg',b'not an image',content_type='image/jpeg')
        self.assertEqual(self.client.patch(url,{'image':upload},format='multipart').status_code,400)
