from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers

from .models import Profile
from .permissions import get_role, is_canteen_staff

User = get_user_model()


def get_profile(user):
    # user.profile is cached by Django after the first access, so this is one query per user.
    try:
        return user.profile
    except Profile.DoesNotExist:
        return Profile.objects.create(user=user)


class UserSerializer(serializers.Serializer):
    """What the frontend gets about the current user."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='first_name', read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.SerializerMethodField(help_text='student — студент, staff — сотрудник столовой.')
    course = serializers.SerializerMethodField()
    faculty = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(help_text='Полный URL картинки или null.')

    def get_role(self, user) -> str:
        return get_role(user)

    def get_course(self, user) -> str:
        return get_profile(user).course

    def get_faculty(self, user) -> str:
        return get_profile(user).faculty

    def get_avatar(self, user) -> str | None:
        profile = get_profile(user)
        if not profile.avatar:
            return None
        request = self.context.get('request')
        url = profile.avatar.url
        return request.build_absolute_uri(url) if request is not None else url


class TokensSerializer(serializers.Serializer):
    """The answer of login and registration (only for the API documentation)."""

    access = serializers.CharField(help_text='Для заголовка Authorization: Bearer <access>, живёт 30 минут.')
    refresh = serializers.CharField(help_text='Для /api/auth/refresh/, живёт 7 дней.')
    user = UserSerializer()


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80)
    email = serializers.EmailField(help_text='Почта — это логин.')
    password = serializers.CharField(write_only=True, help_text='Не короче 8 символов и не слишком простой.')

    def validate_email(self, value):
        email = value.strip().lower()
        # The e-mail may be the login of another user or only their Email field (e.g. a superuser).
        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise serializers.ValidationError('Пользователь с такой почтой уже есть.')
        return email

    def validate(self, data):
        # Check the password against Django's password rules (length, too common, ...).
        validate_password(data['password'], User(username=data['email'], email=data['email']))
        return data

    def create(self, validated_data):
        # The email is used as the username, so students log in with their email.
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['name'].strip(),
        )
        get_profile(user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email'].strip()
        # Students registered on the site have the e-mail as the username. Users made with
        # `createsuperuser` or in the admin often have another username ("admin") and the e-mail
        # only in the Email field — they log in with it too. Letter case does not matter.
        candidates = [
            *User.objects.filter(username__iexact=email),
            *User.objects.filter(email__iexact=email).exclude(username__iexact=email),
        ]
        for candidate in candidates:
            user = authenticate(username=candidate.username, password=data['password'])
            if user is not None:
                data['user'] = user
                return data
        raise serializers.ValidationError('Неверная почта или пароль.')


class ProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80, required=False)
    course = serializers.CharField(max_length=80, required=False, allow_blank=True)
    faculty = serializers.CharField(max_length=120, required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False)

    def validate_avatar(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Изображение должно быть не больше 2 МБ.')
        return value

    def update(self, user, validated_data):
        profile = get_profile(user)
        if 'name' in validated_data:
            user.first_name = validated_data['name'].strip()
            user.save(update_fields=['first_name'])
        for field in ('course', 'faculty', 'avatar'):
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        return user


class StaffLoginSerializer(LoginSerializer):
    def validate(self, data):
        data = super().validate(data)
        if not is_canteen_staff(data['user']):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Вход доступен только сотрудникам столовой.')
        return data
