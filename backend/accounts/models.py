from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Student data that the standard Django User does not have."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='пользователь',
    )
    course = models.CharField('курс', max_length=80, blank=True)
    faculty = models.CharField('факультет', max_length=120, blank=True)
    avatar = models.ImageField('аватар', upload_to='avatars/', blank=True)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return f'Профиль {self.user}'
