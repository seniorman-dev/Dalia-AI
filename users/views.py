from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

from core.responses import DaliaResponse
from core.throttles import LoginThrottle, RegisterThrottle
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    GoogleAuthSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a user.
    This is what gets sent back to Flutter frontend.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return DaliaResponse.error(
                message="Registration failed",
                errors=serializer.errors
            )
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return DaliaResponse.success(
            data={
                'user': UserSerializer(user).data,
                'tokens': tokens
            },
            message="Account created successfully",
            status=201
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return DaliaResponse.error(message="Login failed",errors=serializer.errors)

        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if not user:
            return DaliaResponse.error(
                message="Invalid email or password",
                status=401
            )

        tokens = get_tokens_for_user(user)
        return DaliaResponse.success(
            data={
                'user': UserSerializer(user).data,
                'tokens': tokens
            },
            message="Login successful"
        )


class GoogleAuthView(APIView):
    """
    Flutter sends the Google id_token after Google sign-in.
    We verify it server-side and return our own JWT.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return DaliaResponse.error(errors=serializer.errors)

        try:
            # Verify the Google token
            google_data = id_token.verify_oauth2_token(
                serializer.validated_data['id_token'],
                google_requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
        except ValueError:
            return DaliaResponse.error(
                message="Invalid Google token",
                status=401
            )

        email = google_data.get('email')
        full_name = google_data.get('name', '')

        # Get or create the user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'full_name': full_name,
                'account_type': 'google',
            }
        )

        tokens = get_tokens_for_user(user)
        return DaliaResponse.success(
            data={
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'is_new_user': created
            },
            message="Google login successful"
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        return DaliaResponse.success(
            data=UserSerializer(request.user).data
        )