from colorfield.fields import ColorField
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User


class Tag(models.Model):
    """ Модель тегов для рецептов."""
    name = models.CharField(
        verbose_name='Название тега',
        max_length=200,
        unique=True
    )
    color = ColorField(
        verbose_name='Цвет в HEX-кодировке',
        format='hex',
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message='Введенное значение не является цветом в формате HEX'
            )
        ],
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='Короткое имя',
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингридиента для рецепта """
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        db_index=True
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Еденицы измерения'
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """ Модель рецепта. """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200,
        blank=False,
    )
    image = models.ImageField(
        upload_to='recipes/image/',
        verbose_name='Картинка',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингридиенты',
        through='RecipeIngredient'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Продолжительность готовки',
        validators=[
            MinValueValidator(
                1, message='Минимальное время приготовления - 1 минута.'
            ),
            MaxValueValidator(
                300, message='Продолжительность готовки не более 5 часов'
            )
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class UserRecipe(models.Model):
    """Абстрактная модель списка рецептов пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique'
            )
        ]

    def __str__(self):
        return f'{self.user} :: {self.recipe}'


class FavoriteRecipe(UserRecipe):
    """ Модель добавление в избраное. """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                            )
    recipe =  models.ForeignKey(Recipe,
                             on_delete=models.CASCADE,
                             )


class ShoppingCart(UserRecipe):
    """ Модель рецепта для списка покупок пользователя."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    recipe =  models.ForeignKey(Recipe,
                             on_delete=models.CASCADE,
                             )


class RecipeIngredient(models.Model):
    """ Связь рецепта с ингредиентами и их количеством! """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное количество - 1.')
        ],
        verbose_name='Количество ингредиента',
        blank=False,
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Количество'
        verbose_name_plural = 'Количество'

    def __str__(self):
        return (
            f'{self.ingredient.name} – {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )
