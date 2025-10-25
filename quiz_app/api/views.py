from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from quiz_app.api.serializers import QuizSerializer
from quiz_app.models import Quiz
from quiz_app.api.permissions import IsOwner


class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]





class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
