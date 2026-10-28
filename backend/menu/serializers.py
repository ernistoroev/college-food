from rest_framework import serializers

from .models import Category, Dish

MAX_IMAGE_SIZE = 5 * 1024 * 1024


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'order']


class DishSerializer(serializers.ModelSerializer):
    """
    Reading: everything the dish card needs, with the category name next to its id.
    Writing (staff): send `category` as an id; the photo goes as a file in multipart/form-data.
    """

    category_name = serializers.CharField(source='category.name', read_only=True)
    rating = serializers.SerializerMethodField(help_text='Средняя оценка по видимым отзывам, null — отзывов нет.')
    reviews_count = serializers.SerializerMethodField(help_text='Сколько видимых отзывов о блюде.')

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
            'is_available',
            'image',
            'category',
            'category_name',
            'rating',
            'reviews_count',
        ]

    # rating and reviews_count are counted by the database (annotate in DishViewSet.get_queryset).
    def get_rating(self, dish) -> float | None:
        rating = getattr(dish, 'rating', None)
        return round(rating, 1) if rating is not None else None

    def get_reviews_count(self, dish) -> int:
        return getattr(dish, 'reviews_count', 0)

    def validate_image(self, value):
        if value and value.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError('Фото должно быть не больше 5 МБ.')
        return value


class DishAvailabilitySerializer(serializers.ModelSerializer):
    """Only for PATCH /api/dishes/{id}/availability/."""

    class Meta:
        model = Dish
        fields = ['is_available']
        extra_kwargs = {'is_available': {'required': True}}
