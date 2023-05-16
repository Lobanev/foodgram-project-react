from django.http import HttpResponse
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
                          RecipeReadSerializer, RecipeSnippetSerializer,
                          TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Отображение вывода тегов """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    # pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение вывода ингредиентов """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    # pagination_class = None
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
                serializer = RecipeSnippetSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
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
                serializer = RecipeSnippetSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
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
        Список ингредиентов
        для рецептов из корзины пользователя.
        """
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shoppingcart__user=request.user)
            .values('ingredient__name',
                    'ingredient__measurement_unit', 'amount')
        )
        goods = {}
        for good in ingredients:
            name = good.get('ingredient__name')
            unit = good.get('ingredient__measurement_unit')
            amount = good.get('amount')
            key = f'{name}|{unit}'
            if key in goods.keys():
                goods[key] += amount
            else:
                goods[key] = amount
        text = [f'Cписок покупок пользователя:\n {request.user.first_name}']
        for name_and_unit, amount in goods.items():
            name, unit = name_and_unit.split('|')
            text.append(f'\n-- {name} - {amount} в ({unit})')
        filename = "Shopping_Cart_list.txt"
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class CustomUserViewSet(UserViewSet):
    """
    Класс представления пользователя.
    И подписок пользователей на других пользователей.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        """
        Подписывает пользователя request.user на
        пользователя с идентификатором pk,
        если метод POST, или отписывает пользователя
        request.user от пользователя с идентификатором pk,
        если метод DELETE.
        """
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = FollowSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    "Вы уже подписаны", status=status.HTTP_400_BAD_REQUEST)
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
