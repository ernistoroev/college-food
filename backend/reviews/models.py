from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from menu.models import Dish


class Review(models.Model):
    """A review of a dish, or of the canteen in general when dish is empty."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='пользователь',
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        verbose_name='блюдо',
        help_text='Пусто — отзыв о столовой в целом.',
    )
    rating = models.PositiveSmallIntegerField(
        'оценка', validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField('текст', max_length=1000)
    is_visible = models.BooleanField(
        'показывать', default=True, help_text='Снимите галочку, чтобы скрыть отзыв от студентов.'
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']
        constraints = [
            # One review per dish from one user. Reviews of the canteen (dish is empty) are not limited.
            models.UniqueConstraint(
                fields=['user', 'dish'],
                condition=models.Q(dish__isnull=False),
                name='one_review_per_dish_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.user} — {self.rating}★'
