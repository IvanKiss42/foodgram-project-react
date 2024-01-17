from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import generics
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import AccessToken
from django.db import IntegrityError
from django.conf import settings
from djoser import utils
from djoser.views import TokenCreateView
from rest_framework.authtoken.models import Token

from api.permissions import (IsAdminPermission,
                             IsAdminUserOrReadOnly,
                             IsAuthorAdminSuperuserOrReadOnlyPermission,)
from .serializers import (TokenSerializer, UserCreateSerializer,
                          UsersSerializer, SetPasswordSerializer)
from user.models import User


class UsersView(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""

    serializer_class = UsersSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'id'
    search_fields = ('id',)
    http_method_names = ('get', 'post', 'patch', 'delete')
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
                username=username, email=email)
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
        serializer_for_response = UsersSerializer(user)
        return Response(serializer_for_response.data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False,
            methods=['get', 'patch'],
            url_path='me',
            url_name='me',
            permission_classes=(permissions.IsAuthenticated,))
    def about_me(self, request):
        if request.method == 'PATCH':
            serializer = UserCreateSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserCreateSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
            detail=False,
            methods=['post',],
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
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        username = kwargs.get('username')

        if username == 'me':
            return Response(
                {'detail': 'Вы не можете изменять профиль PATCH-запросом.'},
                status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_object()

        new_username = request.data.get('username')
        new_email = request.data.get('email')

        if new_username == 'me':
            return Response(
                {'detail': 'Нельзя установить `username` в "me" через PATCH.'},
                status=status.HTTP_400_BAD_REQUEST)

        if (
            new_username and User.objects.filter(username=new_username)
            .exclude(id=instance.id).exists()
        ):
            return Response(
                {'detail': 'Это имя пользователя уже существует.'},
                status=status.HTTP_400_BAD_REQUEST)

        if new_email:
            if (
                User.objects.filter(email=new_email)
                .exclude(id=instance.id).exists()
            ):
                return Response(
                    {'detail': 'Этот адрес электронной почты уже занят.'},
                    status=status.HTTP_400_BAD_REQUEST)

        new_role = request.data.get('role')
        if new_role:
            instance.role = new_role
            instance.save()

        serializer = UserCreateSerializer(
            instance,
            data=request.data,
            partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=instance.role)

        return Response(serializer.data, status=status.HTTP_200_OK)


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
        return Response({'token': str(token)}, status=status.HTTP_201_CREATED)
