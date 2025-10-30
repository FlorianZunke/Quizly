from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from quiz_app.api.serializers import QuizSerializer
from quiz_app.models import Quiz
from quiz_app.api.permissions import IsOwner


class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    def perform_create(self, serializer):
        """
        Wird aufgerufen, wenn ein neues Quiz per POST erstellt wird.
        """
        quiz = serializer.save(owner=self.request.user)

        return quiz


class MyQuizzesListView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Gibt nur die Quizzes des angemeldeten Benutzers zurück.
        """
        user = self.request.user
        return Quiz.objects.filter(owner=user)



class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
