from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'dish', 'rating', 'text', 'is_visible', 'created_at']
    # Staff hide a review right in the list.
    list_editable = ['is_visible']
    list_filter = ['is_visible', 'rating', 'dish', 'created_at']
    search_fields = ['text', 'user__username', 'user__first_name']
