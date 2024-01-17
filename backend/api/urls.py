from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

import menu.views
import user.views

v1_router = routers.DefaultRouter()
v1_router.register('users', user.views.UsersView, basename='users')
v1_router.register('recipes', menu.views.RecipeView, basename='recipes')
v1_router.register('tags', menu.views.TagView, basename='tags')
v1_router.register('ingredients', menu.views.IngredientView,
                   basename='ingredients')

urlpatterns = [
    path('auth/token/login/', user.views.TokenLoginView.as_view(
        {'post': 'login'})
    ),
    path('', include(v1_router.urls)),
    url('auth/', include('djoser.urls.authtoken')),
]
