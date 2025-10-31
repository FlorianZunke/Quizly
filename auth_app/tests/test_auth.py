from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthViewsTest(APITestCase):

    def setUp(self):
        self.registration_url = reverse("register")
        self.login_url = reverse("login")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
        
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "confirmed_password": "testpassword123"
        }
        
    def get_user_create_data(self):
        """Helper method to get user data without confirmed_password"""
        return {
            "username": self.user_data["username"],
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }

    def test_registration_success(self):
        response = self.client.post(self.registration_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "User created successfully!")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_login_sets_cookies(self):
        User.objects.create_user(**self.get_user_create_data())

        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpassword123"
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertEqual(response.data["detail"], "Login successfully")

    def test_refresh_token_success(self):
        user = User.objects.create_user(**self.get_user_create_data())
        login_response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpassword123"
        })

        refresh_token = login_response.cookies["refresh_token"].value
        self.client.cookies["refresh_token"] = refresh_token

        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertEqual(response.data["detail"], "Token refreshed")

    def test_refresh_token_missing_cookie(self):
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Refresh token not found in cookies.")

    def test_logout_clears_cookies(self):
        user = User.objects.create_user(**self.get_user_create_data())
        login_response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpassword123"
        })

        refresh_token = login_response.cookies["refresh_token"].value
        access_token = login_response.cookies["access_token"].value

        self.client.cookies["access_token"] = access_token
        self.client.cookies["refresh_token"] = refresh_token

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
        )

        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

class AuthViewsNegativeTest(APITestCase):

    def setUp(self):
        self.registration_url = reverse("register")
        self.login_url = reverse("login")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "confirmed_password": "testpassword123"
        }
        
    def get_user_create_data(self):
        """Helper method to get user data without confirmed_password"""
        return {
            "username": self.user_data["username"],
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }

    def test_registration_missing_fields(self):
        response = self.client.post(self.registration_url, {
            "email": "test@example.com",
            "password": "testpassword123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

        response = self.client.post(self.registration_url, {
            "username": "testuser",
            "email": "test@example.com",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_invalid_email(self):
        response = self.client.post(self.registration_url, {
            "username": "testuser",
            "email": "not-an-email",
            "password": "testpassword123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_invalid_credentials(self):
        User.objects.create_user(**self.get_user_create_data())

        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.login_url, {
            "username": "wronguser",
            "password": "testpassword123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)