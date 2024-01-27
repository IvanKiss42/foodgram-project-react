from django.contrib import admin

from .models import Ingredient, Tag, Recipe, ShoppingCart, Favorite


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'pub_date',
        'cooking_time',
        'author',
        'favorites',
    )
    search_fields = ('name', 'author__username', 'tags')
    list_filter = ('name', 'author__username', 'tags')
    list_editable = ('name', )
    empty_value_display = '-пусто-'

    def favorites(self, obj):
        count = 0
        if Favorite.objects.filter(recipe=obj).exists():
            count = Favorite.objects.filter(recipe=obj).count()
        return count


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
