from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile

User = get_user_model()


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


class UserSerializer(serializers.Serializer):
    """What the frontend gets about the current user."""

    def to_representation(self, user):
        profile = get_profile(user)
        request = self.context.get('request')
        avatar = None
        if profile.avatar:
            avatar = profile.avatar.url
            if request is not None:
                avatar = request.build_absolute_uri(avatar)
        return {
            'id': user.id,
            'name': user.first_name,
            'email': user.email,
            'course': profile.course,
            'faculty': profile.faculty,
            'avatar': avatar,
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(username=email).exists():
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
        user = authenticate(username=data['email'].strip().lower(), password=data['password'])
        if user is None:
            raise serializers.ValidationError('Неверная почта или пароль.')
        data['user'] = user
        return data


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
