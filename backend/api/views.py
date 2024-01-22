from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.authtoken.models import Token

from .permissions import IsAuthorAdminSuperuserOrReadOnlyPermission
from .serializers import (TokenSerializer, UserCreateSerializer,
                          UsersSerializer, SetPasswordSerializer,
                          SubscriptionSerializer, ShowSubscriptionsSerializer,
                          RecipeSerializer, TagSerializer,
                          IngredientSerialiser, ShoppingCartSerializer,
                          CreateRecipeSerializer, FavoriteSerializer,
                          RecipeIngredient,
                          UserpresentationAfterCreateSerializer)
from menu.models import (Recipe, Tag, Ingredient, Favorite,
                         ShoppingCart)
from user.models import User, Subscription
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination, SubscriptionLimitPagination


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
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')

        try:
            user, created = User.objects.get_or_create(
                username=username,
                email=email,
                last_name=serializer.validated_data.get('last_name'),
                first_name=serializer.validated_data.get('last_name'),
                password=serializer.validated_data.get('password'),
            )
        except IntegrityError:
            existing_user = User.objects.filter(username=username).first()
            existing_email = User.objects.filter(email=email).first()

            error_response = {}

            if existing_user:
                error_response['username'] = ["Такой логин уже существует"]

            if existing_email:
                error_response['email'] = ["Такой email уже существует"]

            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        user.save()
        serializer_for_response = UserpresentationAfterCreateSerializer(user)
        return Response(serializer_for_response.data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False,
            methods=['get', 'patch'],
            url_path='me',
            url_name='me',
            permission_classes=(permissions.IsAuthenticated,))
    def about_me(self, request):
        if request.method == 'PATCH':
            serializer = UsersSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
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


class SubscribeView(APIView):
    """Операция подписки и отписки."""

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SubscriptionLimitPagination

    def post(self, request, id):
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        if Subscription.objects.filter(
           user=request.user, author=author).exists():
            subscription = get_object_or_404(
                Subscription, user=request.user, author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShowSubscriptionsView(ListAPIView):
    """ Отображение подписок."""

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SubscriptionLimitPagination

    def get(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        serializer = ShowSubscriptionsSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeView(viewsets.ModelViewSet):
    """Отображение рецептов и действия с ними."""

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


class TagView(viewsets.ModelViewSet):
    """Отображение тэгов."""

    http_method_names = ('get', )
    permission_classes = (permissions.AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientView(viewsets.ModelViewSet):
    """Отображение ингридиентов."""

    http_method_names = ('get', )
    permission_classes = (permissions.AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    pagination_class = None
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class FavoriteView(APIView):
    """ Добавление/удаление рецепта из избранного. """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }
        if not Favorite.objects.filter(
           user=request.user, recipe__id=id).exists():
            serializer = FavoriteSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if Favorite.objects.filter(
           user=request.user, recipe=recipe).exists():
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartView(APIView):
    """Добавление рецепта в корзину или его удаление."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }
        recipe = get_object_or_404(Recipe, id=id)
        if not ShoppingCart.objects.filter(
           user=request.user, recipe=recipe).exists():
            serializer = ShoppingCartSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if ShoppingCart.objects.filter(
           user=request.user, recipe=recipe).exists():
            ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def download_shopping_cart(request):
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
    response = HttpResponse(ingredient_list, 'Content-Type: application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file}.pdf"'
    return response
