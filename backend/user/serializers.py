from django.core.validators import MaxLengthValidator
from rest_framework import serializers

from .models import User


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор для токена."""

    password = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('password', 'email')


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователей."""

    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True,
        validators=[MaxLengthValidator(limit_value=150)]
    )

    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[MaxLengthValidator(limit_value=254)]
    )

    first_name = serializers.CharField(
        max_length=150,
        required=True,
        validators=[MaxLengthValidator(limit_value=150)]
    )

    last_name = serializers.CharField(
        max_length=150,
        required=True,
        validators=[MaxLengthValidator(limit_value=150)]
    )

    password = serializers.CharField(
        max_length=50,
        required=True,
        validators=[MaxLengthValidator(limit_value=50)]
    )

    class Meta:
        model = User
        fields = ('username',
                  'email',
                  'first_name',
                  'last_name',
                  'password')

    def validate_username(self, value):
        if value == 'me':
            if self.instance and self.context['request'].method == 'PATCH':
                raise serializers.ValidationError(
                    'Имя пользователя "me" запрещено.'
                )
            elif not self.instance:
                raise serializers.ValidationError(
                    'Имя пользователя "me" запрещено.'
                )
        return value


class UsersSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
        )


class SetPasswordSerializer(serializers.ModelSerializer):
    """Сериализатор для смены пароля."""
    current_password = serializers.CharField(
        max_length=50,
        required=True,
        validators=[MaxLengthValidator(limit_value=50)])
    new_password = serializers.CharField(
        max_length=50,
        required=True,
        validators=[MaxLengthValidator(limit_value=50)])

    class Meta:
        model = User
        fields = ('current_password', 'new_password',)
