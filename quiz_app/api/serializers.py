from rest_framework import serializers

from quiz_app.models import Quiz, Question

class QuizSerializer(serializers.ModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "questions"]


    def create(self, validated_data):
        from quiz_app.api.utils import generate_quiz_from_video

        quiz = Quiz.objects.create(
            title="Wird generiert...",
            description="Das Quiz wird automatisch erstellt.",
            video_url=validated_data["video_url"],
        )

        generate_quiz_from_video(quiz)

        return quiz


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]

