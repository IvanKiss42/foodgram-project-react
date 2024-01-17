from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Resipe, Tag, Ingridient
from .serializers import ResipeSerializer, TagSerializer, IngridientSerialiser


class RecipeView(viewsets.ModelViewSet):
    queryset = Resipe.objects.all()
    serializer_class = ResipeSerializer
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagView(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = PageNumberPagination


class IngredientView(viewsets.ModelViewSet):
    queryset = Ingridient.objects.all()
    serializer_class = IngridientSerialiser
    pagination_class = PageNumberPagination
