import base64
import webcolors

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Resipe, Tag, Ingridient


class Hex2NameColor(serializers.Field):

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    # color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngridientSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Ingridient
        fields = '__all__'


class ResipeSerializer(serializers.ModelSerializer):
    ingridient = IngridientSerialiser(read_only=True, many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Resipe
        fields = fields = '__all__'
