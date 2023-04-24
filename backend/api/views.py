import datetime

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AuthorPermission
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, FollowSerializer,
                          TagSerializer, CustomUserSerializer)

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

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', ):
            return RecipeReadSerializer
        return CreateRecipeSerializer

    def _user_recipes_controller(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        is_exists = model.objects.filter(user=user, recipe=recipe).exists()
        if request.method == 'POST':
            if is_exists:
                return Response(
                    {'errors': 'Рецепт уже в списке.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(recipe=recipe, user=request.user)
            serializer = ShoppingCartSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not is_exists:
            return Response(
                {'errors': 'Рецепт не в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_recipes = model.objects.filter(user=user, recipe=recipe)
        user_recipes.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        context = {"request": request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self._user_recipes_controller(request, pk, ShoppingCart)

    @action(methods=['GET'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shop_recipes_ids = request.user.shoprecipes.all().values('recipe')
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
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
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
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)