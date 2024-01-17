from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from menu.models import Resipe


class User(AbstractUser):
    """Модель пользователя."""

    ADMIN = 'admin'
    USER = 'user'

    USER_ROLE = (
        (USER, 'user'),
        (ADMIN, 'admin'),
    )

    username = models.CharField(
        max_length=150,
        verbose_name='Уникальный юзернейм',
        help_text='Укажите юзернейм',
        unique=True,
        validators=([RegexValidator(regex=r'^[\w.@+-]+\z')])
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Адрес электронной почты',
        help_text='Укажите e-mail',
        unique=True
    )
    confirmation_code = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='Проверочный код'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Ваше Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Ваша Фамилия'
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль',
        blank=False,
        help_text='Ваш Пароль'
    )
    role = models.CharField(
        max_length=100,
        verbose_name='Роль',
        choices=USER_ROLE,
        default=USER,
        help_text='Пользователь'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.is_staff or self.role == User.ADMIN

    def __str__(self):
        return self.username


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resipe = models.ForeignKey(Resipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'resipe')
