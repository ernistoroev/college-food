from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    A review as the frontend gets it: names of the author and the dish next to their ids.
    A student sends {rating, text} and, for a review of a dish, its id in `dish`.
    """

    user_name = serializers.CharField(source='user.first_name', read_only=True)
    dish_name = serializers.CharField(source='dish.name', read_only=True, default=None)

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'dish', 'dish_name', 'rating', 'text', 'is_visible', 'created_at']
        read_only_fields = ['id', 'user_name', 'dish_name', 'is_visible', 'created_at']

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Напиши текст отзыва.')
        return value

    def validate_dish(self, dish):
        # Checked here too, so the student gets a clear message instead of a database error.
        user = self.context['request'].user
        if dish is not None and Review.objects.filter(user=user, dish=dish).exists():
            raise serializers.ValidationError('Ты уже оставил отзыв об этом блюде.')
        return dish


class ReviewModerationSerializer(serializers.ModelSerializer):
    """What staff can change in a review: only whether it is shown."""

    class Meta:
        model = Review
        fields = ['is_visible']
        extra_kwargs = {'is_visible': {'required': True}}
