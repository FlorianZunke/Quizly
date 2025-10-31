from django.urls import path
from .views import QuizListCreateView, QuizDetailView

urlpatterns = [
   path("createQuiz/", QuizListCreateView.as_view(), name="quiz-list-create"),
   path("quizzes/", QuizListCreateView.as_view(), name="quiz-list"),
   path("quizzes/<int:pk>/", QuizDetailView.as_view(), name="my-quizzes"),
]