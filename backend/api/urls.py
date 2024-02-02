from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

from .views import (RecipeView, TagView, IngredientView,
                    TokenLoginView, UsersView)

app_name = 'api'

v1_router = routers.DefaultRouter()
v1_router.register('users', UsersView, basename='users')
v1_router.register('recipes', RecipeView, basename='recipes')
v1_router.register('tags', TagView, basename='tags')
v1_router.register('ingredients', IngredientView, basename='ingredients')

urlpatterns = [
    path('auth/token/login/', TokenLoginView.as_view(
        {'post': 'login'})),
    path('', include(v1_router.urls)),
    url('auth/', include('djoser.urls.authtoken')),
]
