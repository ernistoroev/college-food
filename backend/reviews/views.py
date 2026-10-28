from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import IsCanteenStaff, IsStudentOrReadOnly, is_canteen_staff

from .models import Review
from .serializers import ReviewModerationSerializer, ReviewSerializer

TAG = 'Отзывы'
MODERATION = extend_schema(
    tags=[TAG], summary='Скрыть или показать отзыв', request=ReviewModerationSerializer, responses=ReviewSerializer,
    description='Меняется только `is_visible`. Только сотрудник столовой.',
)


def filter_by_dish(queryset, value):
    """?dish=<id> — reviews of one dish, ?dish=none — reviews of the canteen in general."""
    if value == 'none':
        return queryset.filter(dish__isnull=True)
    if value and value.isdigit():
        return queryset.filter(dish_id=value)
    return queryset


@extend_schema_view(
    list=extend_schema(
        tags=[TAG], summary='Отзывы',
        description='Студенты и гости видят только видимые отзывы, сотрудник — все (с `is_visible`).',
        parameters=[OpenApiParameter('dish', OpenApiTypes.STR,
                                     description='id блюда — отзывы о нём; `none` — отзывы о столовой в целом.')],
    ),
    retrieve=extend_schema(tags=[TAG], summary='Один отзыв'),
    create=extend_schema(
        tags=[TAG], summary='Оставить отзыв',
        description='Только студент. Без `dish` — отзыв о столовой; с `dish` — о блюде, один на блюдо.',
    ),
    update=MODERATION,
    partial_update=MODERATION,
    destroy=extend_schema(tags=[TAG], summary='Удалить отзыв', description='Только сотрудник столовой.'),
)
class ReviewViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    GET    /api/reviews/      — everyone; students and guests see only visible reviews, staff see all;
                                filter ?dish=<id> or ?dish=none;
    POST   /api/reviews/      — only a logged-in student {rating, text, dish?};
    PATCH  /api/reviews/{id}/ — only staff {is_visible}: hide or show a review;
    DELETE /api/reviews/{id}/ — only staff.
    """

    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action == 'create':
            return [IsStudentOrReadOnly()]
        return [IsCanteenStaff()]

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'dish')
        if getattr(self, 'swagger_fake_view', False):  # the API documentation is being built
            return queryset
        # Hidden reviews are visible only to staff, who moderate them.
        if not is_canteen_staff(self.request.user):
            queryset = queryset.filter(is_visible=True)
        return filter_by_dish(queryset, self.request.query_params.get('dish'))

    def perform_create(self, serializer):
        # The author is always the current user, not something sent by the browser.
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        # In form data a missing checkbox would mean False; require the field explicitly.
        if 'is_visible' not in request.data:
            return Response({'is_visible': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ReviewModerationSerializer(review, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReviewSerializer(review, context=self.get_serializer_context()).data)
