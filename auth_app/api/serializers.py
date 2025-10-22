from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirmed_password', 'email']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        """
        Validate that the confirmed password matches the password.
        """
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """
        Validate that the email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """
        Create a new user account.
        """
        pw = self.validated_data['password']

        account = User(email=self.validated_data['email'], username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account
    

User = get_user_model()
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to include user data in the token response.
    """
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Ungültiger Benutzername oder Passwort")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Ungültige Benutzername oder Passwort")
        
        data = super().validate({"username": user.username, "password": password})
        return data