import datetime

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AuthorPermission
from .serializers import (CreateRecipeSerializer, CustomUserSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeReadSerializer, TagSerializer)
from .utils import PDFGenerator


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Отображение вывода тегов """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение вывода ингредиентов """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = None
    filter_backends = (IngredientFilter, )
    search_fields = ('^name', )


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вывод работы с рецептами """
    queryset = Recipe.objects.all()
    permission_classes = (AuthorPermission, )
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    serializer_class = CreateRecipeSerializer
    filter_backends = (DjangoFilterBackend, )

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        """
        Возвращает класс сериализатора, соответствующий типу запроса.
        """
        if self.request.method in ('POST', 'PATCH', ):
            return CreateRecipeSerializer
        return RecipeReadSerializer

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        """
           Добавляет рецепт в список избранных для текущего пользователя.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            favorite, created = FavoriteRecipe.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                return Response(status=status.HTTP_201_CREATED)
            return Response({'detail': 'Такая запись уже есть в избранном'},
                            status.HTTP_400_BAD_REQUEST
                            )

        favorite_recipe = FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        )
        if favorite_recipe.exists():
            favorite_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Запись не в избранном'},
                        status.HTTP_400_BAD_REQUEST
                        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        """
        Возвращает список рецептов,
        добавленных в корзину пользователя
        с идентификатором pk.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            shop, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                return Response(status=status.HTTP_201_CREATED)
            return Response({'detail': 'Такая запись уже есть в корзине'},
                            status.HTTP_400_BAD_REQUEST
                            )

        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        )
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Запись нет в корзине'},
                        status.HTTP_400_BAD_REQUEST
                        )

    @action(methods=['GET'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Генерирует PDF-файл со списком ингредиентов
        для рецептов из корзины пользователя.
        """
        shop_recipes_ids = request.user.shoppingcart.all().values('recipe')
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe_id__in=shop_recipes_ids)
            .select_related('ingredient')
            .values('ingredient__name')
            .annotate(total=Sum('amount'))
            .values(
                'ingredient__name',
                'total',
                'ingredient__measurement_unit'
            )
        )

        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(
                f'{ingredient.get("ingredient__name").capitalize()} '
                f'({ingredient.get("ingredient__measurement_unit")}) — '
                f'{ingredient.get("total")}'
            )
        return FileResponse(
            PDFGenerator(ingredients_list),
            as_attachment=True,
            filename=f'{request.user} shoplist {datetime.date.today()}.pdf'
        )


class FollowViewSet(UserViewSet):
    """
    Класс представления для подписок пользователей на других пользователей.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
        """
        Подписывает пользователя request.user на
        пользователя с идентификатором pk,
        если метод POST, или отписывает пользователя
        request.user от пользователя с идентификатором pk,
        если метод DELETE.
        """
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            serializer = FollowSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(
                Follow, user=user, author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """
        Возвращает список пользователей,
        на которых подписан пользователь request.user.
        """
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
