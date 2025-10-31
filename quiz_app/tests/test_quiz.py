from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

from quiz_app.models import Quiz

User = get_user_model()

from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from quiz_app.models import Quiz

User = get_user_model()

class QuizViewsPositiveTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )

        self.quiz = Quiz.objects.create(
            title="Test Quiz",
            description="Beschreibung",
            owner=self.user,
            url="https://www.youtube.com/watch?v=example"
        )

        self.list_create_url = reverse("quiz-list-create")
        self.detail_url = lambda pk: reverse("my-quizzes", args=[pk])

    @patch("quiz_app.api.utils.generate_quiz_data_from_video")
    def test_create_quiz_authenticated_user(self, mock_generate):
        """
        Mock generate_quiz_data_from_video to avoid actual downloads/transcription.
        """
        self.client.force_authenticate(user=self.user)

        mock_generate.return_value = {
            "success": True,
            "data": {
                "title": "Neues Quiz",
                "description": "Beschreibung",
                "questions": [
                    {
                        "question_title": "Q1",
                        "question_options": ["A", "B", "C", "D"],
                        "answer": "A"
                    }
                ]
            }
        }

        data = {
            "url": "https://www.youtube.com/watch?v=GPGk5QTBkLs"
        }

        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Quiz.objects.filter(title="Neues Quiz", owner=self.user).exists())

    def test_list_quizzes_authenticated_user(self):
        """
        List quizzes for authenticated user.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Test Quiz")

    def test_retrieve_quiz_detail_owner(self):
        """
        Retrieve quiz detail for owner.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url(self.quiz.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Quiz")

    def test_update_quiz_detail_owner(self):
        """
        Update quiz detail for owner.
        """
        self.client.force_authenticate(user=self.user)
        data = {"title": "Updated Title"}
        response = self.client.patch(self.detail_url(self.quiz.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, "Updated Title")

    def test_delete_quiz_detail_owner(self):
        """
        Delete quiz for owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url(self.quiz.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())


class QuizViewsNegativeTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpassword"
        )

        self.quiz = Quiz.objects.create(
            title="Test Quiz",
            description="Beschreibung",
            owner=self.user,
            url="https://www.youtube.com/watch?v=example"
        )

        self.list_create_url = reverse("quiz-list-create")
        self.detail_url = lambda pk: reverse("my-quizzes", args=[pk])

    def test_create_quiz_missing_url(self):
        """
        Create a new quiz with missing required URL field.
        """
        self.client.force_authenticate(user=self.user)
        data = {}  # kein URL-Feld
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)

    def test_list_quizzes_unauthenticated(self):
        """
        List quizzes without authentication.
        """
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_quiz_not_owner(self):
        """
        Retrieve quiz detail for non-owner.
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.detail_url(self.quiz.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_quiz_not_owner(self):
        """
        Update quiz detail for non-owner.
        """
        self.client.force_authenticate(user=self.other_user)
        data = {"title": "Hack Title"}
        response = self.client.patch(self.detail_url(self.quiz.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_quiz_not_owner(self):
        """
        Delete quiz for non-owner.
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.detail_url(self.quiz.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
