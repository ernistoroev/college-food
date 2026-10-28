from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'name', 'rating', 'text', 'created_at']
        read_only_fields = ['id', 'name', 'created_at']

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Напиши текст отзыва.')
        return value
