from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_schema_is_available(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'College Food API', response.content)

    def test_swagger_page_is_available(self):
        self.assertEqual(self.client.get('/api/docs/').status_code, 200)


class FrontendRoutesTests(APITestCase):
    def test_staff_panel_pages_open_the_react_site(self):
        home = b''.join(self.client.get('/'))
        for url in ['/staff', '/staff/', '/staff/login', '/staff/orders']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response), home)

    def test_staff_api_and_django_admin_are_not_the_react_site(self):
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 401)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get('/staffroom').status_code, 404)
