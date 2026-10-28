from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """GET /api/reviews/ — everyone can read; POST {rating, text} — only logged-in students."""

    queryset = Review.objects.select_related('user')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # The author is always the current user, not something sent by the browser.
        serializer.save(user=self.request.user)
