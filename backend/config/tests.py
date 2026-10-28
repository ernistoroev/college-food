from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_schema_is_available(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'College Food API', response.content)

    def test_swagger_page_is_available(self):
        self.assertEqual(self.client.get('/api/docs/').status_code, 200)
