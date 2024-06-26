import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from user.models import User, Subscription
from menu.models import (Recipe, Tag, Ingredient, Favorite,
                         RecipeIngredient, ShoppingCart, RecipeTag)


class Base64ImageField(serializers.ImageField):
    """Поле для отображения картинки."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор для токена."""

    password = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('password', 'email')


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователей."""

    class Meta:
        model = User
        fields = ('username',
                  'id',
                  'email',
                  'first_name',
                  'last_name',
                  'password')

    def validate_username(self, value):
        if value.lower() == 'me':
            if self.instance and self.context['request'].method == 'PATCH':
                raise serializers.ValidationError(
                    'Имя пользователя "me" запрещено!'
                )
            if not self.instance:
                raise serializers.ValidationError(
                    'Имя пользователя "me" запрещено!'
                )
        return value

    def create(self, validated_data):
        return User.objects.create(**validated_data)


class UserPresentationAfterCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения создного пользователя."""

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name'
                  )


class UsersSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class SetPasswordSerializer(serializers.ModelSerializer):
    """Сериализатор для смены пароля."""
    current_password = serializers.CharField(
        max_length=50,
        required=True)
    new_password = serializers.CharField(
        max_length=50,
        required=True)

    class Meta:
        model = User
        fields = ('current_password', 'new_password',)

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                "Старый и новый пароли не должны совпадать!"
            )
        return data


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    class Meta:
        model = Subscription
        fields = ('user', 'author', )
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(
            instance.author,
            context={'request': self.context.get('request')}).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerialiser(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи ингредиента и рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализотор для отображения рецепта."""

    tags = TagSerializer(many=True)
    author = UsersSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = fields = ('id', 'tags', 'author', 'name', 'text', 'image',
                           'ingredients', 'is_favorited',
                           'is_in_shopping_cart', 'cooking_time',)

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class AddIngredientToRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиента в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор создания и обновления рецепта."""

    author = UsersSerializer(read_only=True)
    ingredients = AddIngredientToRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name', 'text', 'image',
                  'ingredients', 'cooking_time',)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError({
                'ingredients': 'Необходимо указать ингридиенты'
            })
        ingredients = []
        for ingredient in value:
            amount = ingredient['amount']
            get_object_or_404(
                Ingredient.objects.filter(id=ingredient['id'])
            )
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Невозможно указать количество меньше 1'
                })
            if ingredient['id'] in ingredients:
                raise serializers.ValidationError({
                    'ingredient': 'Нельзя повторять ингридиенты!'
                })
            ingredients.append(ingredient['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError({
                'ingredients': 'Необходимо указать минимум один тэг'
            })
        tags = []
        for tag in value:
            if tag in tags:
                raise serializers.ValidationError({
                    'ingredient': 'Нельзя повторять тэги!'
                })
            tags.append(tag)
        return value

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for i in ingredients:
            Ingredient.objects.get(id=i['id'])
            ingredient_list.append(RecipeIngredient(
                ingredient=Ingredient.objects.get(id=i['id']),
                recipe=recipe,
                amount=i['amount']
            ))
        RecipeIngredient.objects.bulk_create(ingredient_list)

    def create_tags(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения избранного."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data
