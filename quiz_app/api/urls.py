from django.urls import path
from .views import QuizListCreateView

urlpatterns = [
   path("createQuiz/", QuizListCreateView.as_view(), name="quiz-list-create"),
   path("quizzes/", QuizListCreateView.as_view(), name="quiz-list-create")
]