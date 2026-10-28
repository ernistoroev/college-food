from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'text', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['text', 'user__username', 'user__first_name']
