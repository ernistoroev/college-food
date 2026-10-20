from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, DishViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('dishes', DishViewSet, basename='dish')

urlpatterns = router.urls
