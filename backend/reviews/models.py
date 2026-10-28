from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='пользователь',
    )
    rating = models.PositiveSmallIntegerField(
        'оценка', validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField('текст', max_length=1000)
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.rating}★'
