from rest_framework import serializers

from quiz_app.models import Quiz, Question
from django.db import transaction


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Question model.
    """
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuizSerializer(serializers.ModelSerializer):
    """
    Basic Serializer for Quiz including questions and URL handling.
    """
    questions = QuestionSerializer(many=True, read_only=True)
    video_url = serializers.URLField(source="url", read_only=True)
    url = serializers.URLField(write_only=True, required=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at",
                  "updated_at", "video_url", "url", "questions"]

    def create(self, validated_data):
        """
        Create a Quiz along with its Questions by generating data from the provided video URL."""
        from quiz_app.api.utils import generate_quiz_data_from_video

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentifizierung erforderlich")

        video_url = validated_data.pop("url", None)
        if not video_url:
            raise serializers.ValidationError("URL ist erforderlich")

        result = generate_quiz_data_from_video(video_url)
        if not result.get("success"):
            raise serializers.ValidationError({"error": "Quiz-Generierung fehlgeschlagen", "details": result.get("error")})

        quiz_data = result.get("data") or {}

        with transaction.atomic():
            """
            If all is well, create Quiz + Questions atomically.
            """
            quiz = Quiz.objects.create(
                title=quiz_data.get("title", "Wird generiert..."),
                description=quiz_data.get("description", ""),
                url=video_url,
                owner=request.user,
            )

            for q in quiz_data.get("questions", []):
                """
                Create Question instances linked to the Quiz.
                """
                Question.objects.create(
                    quiz=quiz,
                    question_title=q.get("question_title", ""),
                    question_options=q.get("question_options", []),
                    answer=q.get("answer", ""),
                )

        return quiz
    

class QuizDetailSerializer(serializers.ModelSerializer):
    """
    Detailed Serializer for Quiz including questions and URL handling, with validation for update operations.
    """
    questions = QuestionSerializer(many=True, read_only=True)
    video_url = serializers.URLField(source="url", read_only=True)
    url = serializers.URLField(write_only=True, required=True)
    
    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "url", "questions"]
        read_only_fields = ["id", "created_at", "updated_at", "video_url", "questions"]

    def validate(self, attrs):
        """
        Validate that only 'title' and 'description' are provided.
        """
        allowed_fields = {"title", "description"}
        input_fields = set(self.initial_data.keys())
        invalid_fields = input_fields - allowed_fields

        if invalid_fields:
            raise serializers.ValidationError({
                "error": f"Ungültige Felder: {', '.join(invalid_fields)}. "
                         f"Erlaubt sind nur: {', '.join(sorted(allowed_fields))}."
            })

        return attrs

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance
