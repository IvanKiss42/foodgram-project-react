from rest_framework.filters import SearchFilter
from django_filters import rest_framework

from menu.models import Tag, Recipe


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(rest_framework.FilterSet):
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug'
    )
    is_favorited = rest_framework.BooleanFilter(method='get_favorite')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def get_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
