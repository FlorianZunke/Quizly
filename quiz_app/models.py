from django.db import models

class Quiz(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField()

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    question_title = models.CharField(max_length=200)
    question_options = models.JSONField()
    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)