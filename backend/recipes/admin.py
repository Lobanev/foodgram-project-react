from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """ Панель администратора управление  ингредиентами """
    list_display = ('name', 'measurement_unit', )
    list_filter = ('name', )
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """ Панель администратора управление тегами """
    list_display = ('name', 'color', 'slug', )
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """ Панель администратора упправление рецептами """
    inlines = [RecipeIngredientInline, ]
    list_display = ('name', 'author', 'favorites',)
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('text', )
    empty_value_display = '-пусто-'

    def favorites(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj).count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """ Панель администратора управление ингредиентами рецепта """
    list_display = ('recipe', 'ingredient', 'amount', )
    list_filter = ('recipe',)


@admin.register(FavoriteRecipe)
class FavoriteRecipesAdmin(admin.ModelAdmin):
    """ Панель администратора избранные рецепты """
    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user')
    search_fields = ('user',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShopListAdmin(admin.ModelAdmin):
    """ Панель администратора списка покупок """
    list_display = ('user', 'recipe', )
    list_filter = ('user', )
    search_fields = ('user',)
    empty_value_display = '-пусто-'
