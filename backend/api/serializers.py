from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.validators import ValidationError

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """
        Метод для создания нового пользователя.
        """
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(UserSerializer):
    """ Сериализатор для отображения информации о пользователе."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', )

    def get_is_subscribed(self, obj):
        """
        Метод для определения, подписан ли пользователь
        на текущего пользователя.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра тегов """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для ингредиентов """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class RecipeSnippetSerializer(serializers.ModelSerializer):
    """ Сериализатор отображения избранного """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор подписки"""
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def validate(self, data):
        """
        Метод для проверки валидности данных, введенных при создании подписки.
        """
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author_id).exists():
            raise ValidationError(
                detail='Такая подписка уже существует',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail='Невозможно подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    def get_is_subscribed(self, obj):
        follower = self.context.get('request').user
        if follower.is_anonymous:
            return False
        return Follow.objects.filter(user=follower, author=obj).exists()

    def get_recipes(self, obj):
        """
        Метод для получения списка рецептов пользователя.
        """
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipeSnippetSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """
        Метод для получения количества рецептов пользователя.
        """
        return obj.recipes.count()


class ReadIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор количества игредиента для рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра рецепта """
    author = CustomUserSerializer(read_only=True, many=False)
    tags = TagSerializer(read_only=False, many=True)
    ingredients = ReadIngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ('id', 'author', 'is_favorited',
                            'is_in_shopping_cart',)

    def get_ingredients(self, obj):
        """
        Метод для получения списка ингредиентов, связанных с рецептом.
        """
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return ReadIngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """
        Метод для определения, добавлен ли рецепт в избранное
        текущим пользователем.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Recipe.objects.filter(
            favoriterecipe__user=request.user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Метод для определения, добавлен ли рецепт в корзину
        покупок текущим пользователем.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Recipe.objects.filter(
            shoppingcart__user=request.user, id=obj.id).exists()


class CreateIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор количества игредиента для рецепта."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецепта """
    author = CustomUserSerializer(read_only=True)
    ingredients = CreateIngredientRecipeSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField(max_length=None)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',)

    def validate(self, data):
        """
        Метод для проверки валидности данных, введенных пользователем.
        """
        ingredients = data['ingredients']
        ingredients_set = set(ingredient['id'] for ingredient in ingredients)
        am_message = 'Количество ингредиента должно быть больше или равно 1.'
        ingredient_message = 'Ингредиенты должны быть уникальными.'
        if len(ingredients) != len(ingredients_set):
            raise serializers.ValidationError(
                {'ingredients': ingredient_message}
            )
        for ingredient in ingredients:
            amount = ingredient['amount']
            if int(amount) < 1:
                raise serializers.ValidationError(
                    {'amount': am_message}
                )

        if not data['tags']:
            raise serializers.ValidationError(
                {'tags': 'Выберите хотя бы один тэг.'}
            )
        tag_set = set(data['tags'])
        if len(data['tags']) != len(tag_set):
            raise serializers.ValidationError(
                {'tags': 'Тэги должны быть уникальными.'}
            )

        cook_message = 'Время готовки должно быть не меньше одной минуты'
        if 'cooking_time' not in data or int(data['cooking_time']) <= 0:
            raise serializers.ValidationError(
                {'cooking_time': cook_message}
            )
        return data

    def create_ingredients(self, recipe, ingredients):
        """
        Метод для создания связи между ингредиентами и рецептом.
        """
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic()
    def create(self, validated_data):
        """
        Метод для создания нового рецепта.
        """
        request = self.context.get('request', None)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        """
        Метод для обновления данных рецепта.
        """
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Метод для преобразования объекта рецепта в словарь.
        """
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data
