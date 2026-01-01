# accounts/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsTestCase(APITestCase):
    
    def setUp(self):
        # Only required fields for registration
        self.basic_user_data = {
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "Password123",
        }
    
    def test_index_endpoint(self):
        """Test the health check endpoint"""
        url = reverse('accounts-index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Accounts API working!"})

    def test_user_registration(self):
        """Test registration with only required fields"""
        url = reverse('register')
        response = self.client.post(url, self.basic_user_data, format='json')
        
        # Debug if fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"❌ Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        
        # Verify user was created
        user_exists = User.objects.filter(email=self.basic_user_data['email']).exists()
        self.assertTrue(user_exists)
    
    def test_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        url = reverse('register')
        
        # Test missing email
        data = self.basic_user_data.copy()
        data.pop('email')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing first_name
        data = self.basic_user_data.copy()
        data.pop('first_name')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing last_name
        data = self.basic_user_data.copy()
        data.pop('last_name')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_jwt_login(self):
        """Test JWT token obtain endpoint"""
        # First create a user
        user = User.objects.create_user(
            email="testlogin@example.com",
            first_name="Test",
            last_name="Login",
            password="Password123"
        )
        
        url = reverse('token_obtain_pair')
        data = {
            "email": "testlogin@example.com",
            "password": "Password123"
        }
        
        response = self.client.post(url, data, format='json')
        
        # Debug if fails
        if response.status_code != status.HTTP_200_OK:
            print(f"❌ JWT Login failed: {response.status_code}")
            print(f"❌ Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
    
    def test_protected_endpoint_access(self):
        """Test that protected endpoints require authentication"""
        url = reverse('user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)