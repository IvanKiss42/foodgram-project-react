from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import UniqueConstraint


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
        validators=([RegexValidator(regex=r'^[\w.@+-]+\Z')])
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Адрес электронной почты',
        help_text='Укажите e-mail',
        unique=True
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


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_unique'
            )
        ]    

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
