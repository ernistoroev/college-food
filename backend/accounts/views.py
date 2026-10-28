from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    TokensSerializer,
    UserSerializer,
)

TAG = 'Авторизация'


def tokens_response(user, request, status_code=status.HTTP_200_OK):
    """
    access  — short-lived token for every request: header "Authorization: Bearer <access>";
    refresh — long-lived token to get a new access token at /api/auth/refresh/.
    """
    refresh = RefreshToken.for_user(user)
    data = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user, context={'request': request}).data,
    }
    return Response(data, status=status_code)


class RegisterView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=[TAG], summary='Регистрация студента', request=RegisterSerializer, responses={201: TokensSerializer},
        description='Создаёт аккаунт студента (сотрудником назначают в админке) и сразу выдаёт токены.',
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return tokens_response(user, request, status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=[TAG], summary='Вход', request=LoginSerializer, responses={200: TokensSerializer},
        description='Вход по почте и паролю. В ответе `user.role` — какой интерфейс показывать.',
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return tokens_response(serializer.validated_data['user'], request)


@extend_schema_view(
    post=extend_schema(tags=[TAG], summary='Обновить access-токен',
                       description='Принимает `refresh`, возвращает новый `access`.'),
)
class RefreshView(TokenRefreshView):
    pass


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=[TAG], summary='Текущий пользователь', responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    @extend_schema(
        tags=[TAG], summary='Изменить профиль', request={'multipart/form-data': ProfileUpdateSerializer},
        responses=UserSerializer, description='Любые из полей: name, course, faculty, avatar (файл до 2 МБ).',
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={'request': request}).data)
