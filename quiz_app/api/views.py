from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from quiz_app.api.serializers import QuizSerializer, QuizDetailSerializer
from quiz_app.models import Quiz
from quiz_app.api.permissions import IsOwner


class QuizListCreateView(generics.ListCreateAPIView):
    """
    View to list and create quizzes for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer

    def get_queryset(self):
        """
        returns only the quizzes of the currently logged-in user.
        """
        return Quiz.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Set the quiz owner to the currently logged-in user.
        """
        quiz = serializer.save(owner=self.request.user)

        return quiz



class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update or delete a quiz.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]
