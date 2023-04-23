from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientFilter(SearchFilter):
    """ Фильтр ингредиентов по названию """
    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    """ фильтрация по тегам/избранному/автору/наличию списка покупок! """
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    def get_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favoriterecipes__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoprecipes__user=self.request.user)
        return

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart',)
