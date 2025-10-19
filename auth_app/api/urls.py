from django.urls import path
from .views import RegistrationView, CookieTokenObtainPairView, CookieTokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]