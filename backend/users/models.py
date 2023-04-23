from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q, UniqueConstraint


class User(AbstractUser):
    """Кастомная модель юзера"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=150,
        verbose_name='email',
        unique=True
    )
    username = models.CharField(
        verbose_name='username',
        max_length=254,
        unique=True,
        validators=(UnicodeUsernameValidator(), )
    )

    class Meta:
        ordering = ('username', )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи',

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок пользователей друг на друга."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Автор рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецепта',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id', )
        constraints = [
            UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='no_self_follow'
            )
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
