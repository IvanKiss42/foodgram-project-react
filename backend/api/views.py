from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token

from .permissions import IsAuthorAdminSuperuserOrReadOnlyPermission
from .serializers import (
    TokenSerializer, UserCreateSerializer, UsersSerializer,
    SetPasswordSerializer, ShowSubscriptionsSerializer, SubscriptionSerializer,
    RecipeSerializer, TagSerializer, IngredientSerialiser,
    ShoppingCartSerializer, CreateRecipeSerializer, FavoriteSerializer,
    RecipeIngredient, UserPresentationAfterCreateSerializer
)
from menu.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from user.models import User, Subscription
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination


class UsersView(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""

    serializer_class = UsersSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'id'
    search_fields = ('id',)
    http_method_names = ('get', 'post',)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = User.objects.all()
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(username__icontains=search_query)
        return queryset

    def create(self, request, *args, **kwargs):
        """Создание пользователя."""

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(request.data)
        serializer_for_response = UserPresentationAfterCreateSerializer(user)
        return Response(serializer_for_response.data,
                        status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get', ],
        url_path='me',
        url_name='me',
        permission_classes=(permissions.IsAuthenticated,))
    def about_me(self, request):
        serializer = UsersSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post', ],
        url_path='set_password',
        url_name='set_password',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(seld, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        password = user.password
        password_for_check = serializer.data['current_password']
        if password == password_for_check:
            user.password = serializer.data['new_password']
            user.save()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete', ],
        permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'author': id
            }
            serializer = SubscriptionSerializer(
                data=data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            author = get_object_or_404(User, id=id)
            if Subscription.objects.filter(
               user=request.user, author=author).exists():
                subscription = get_object_or_404(
                    Subscription, user=request.user, author=author
                )
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get', ],
        permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = ShowSubscriptionsSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TokenLoginView(viewsets.ModelViewSet):
    """ViewSet для получения логина."""

    serializer_class = TokenSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ('post',)
    queryset = User.objects.all()

    def login(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data['email']
        user = get_object_or_404(User, email=email)
        password = serializer.data['password']
        if user.password != password:
            raise ValidationError('Неверный пароль')
        token = Token.objects.create(user=user)
        return Response({'auth_token': str(token)},
                        status=status.HTTP_201_CREATED)


class RecipeView(viewsets.ModelViewSet):
    """View для отображение рецептов и действия с ними."""

    permission_classes = (IsAuthorAdminSuperuserOrReadOnlyPermission, )
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitPagination
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend, ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'recipe': pk
            }
            recipe = get_object_or_404(Recipe, id=pk)
            if not ShoppingCart.objects.filter(
               user=request.user, recipe=recipe).exists():
                serializer = ShoppingCartSerializer(
                    data=data, context={'request': request}
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data,
                                    status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            recipe = get_object_or_404(Recipe, id=pk)
        if ShoppingCart.objects.filter(
           user=request.user, recipe=recipe).exists():
            ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'recipe': pk
            }
            if not Favorite.objects.filter(
               user=request.user, recipe__id=pk).exists():
                serializer = FavoriteSerializer(
                    data=data, context={'request': request}
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data,
                                    status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            recipe = get_object_or_404(Recipe, id=pk)
            if Favorite.objects.filter(
               user=request.user, recipe=recipe).exists():
                Favorite.objects.filter(
                    user=request.user, recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get', ],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request,):
        ingredient_list = "Cписок покупок:"
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        for num, i in enumerate(ingredients):
            ingredient_list += (
                f"\n{i['ingredient__name']} - "
                f"{i['amount']} {i['ingredient__measurement_unit']}"
            )
            if num < ingredients.count() - 1:
                ingredient_list += ', '
        file = 'shopping_list'
        response = HttpResponse(ingredient_list,
                                'Content-Type: application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{file}.pdf"'
        return response


class TagView(viewsets.ModelViewSet):
    """View для отображение тэгов."""

    http_method_names = ('get', )
    permission_classes = (permissions.AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientView(viewsets.ModelViewSet):
    """View для отображение ингридиентов."""

    http_method_names = ('get', )
    permission_classes = (permissions.AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    pagination_class = None
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]
