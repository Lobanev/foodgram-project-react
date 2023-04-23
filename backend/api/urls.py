from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, FollowViewSet


router_v1 = routers.DefaultRouter()
router_v1.register(r'users', FollowViewSet, basename='follows')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
