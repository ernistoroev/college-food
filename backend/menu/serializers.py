
from rest_framework import serializers

from .models import Category, Dish


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class DishSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Dish
        fields = [
            'id',
            'name',
            'description',
            'price',
            'weight',
            'weight_unit',
            'portions_today',
            'image',
            'category',
            'category_name',
        ]
