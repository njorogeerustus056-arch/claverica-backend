# accounts/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class AccountsTestCase(APITestCase):
    def test_index_endpoint(self):
        url = reverse('accounts_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Accounts API working!"})

    def test_user_registration(self):
        url = reverse('register')
        data = {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "Password123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("access" in response.data)
        self.assertTrue(User.objects.filter(username="johndoe").exists())
