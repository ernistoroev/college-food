from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, ProfileUpdateSerializer, RegisterSerializer, UserSerializer


def token_response(user, request, status_code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    data = {'token': token.key, 'user': UserSerializer(user, context={'request': request}).data}
    return Response(data, status=status_code)


class RegisterView(APIView):
    """POST /api/auth/register/ {name, email, password} -> {token, user}"""

    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return token_response(user, request, status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ {email, password} -> {token, user}"""

    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return token_response(serializer.validated_data['user'], request)


class LogoutView(APIView):
    """POST /api/auth/logout/ — deletes the token, so it stops working."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — current user; PATCH — update name, course, faculty, avatar."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={'request': request}).data)
