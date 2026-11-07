from rest_framework.routers import DefaultRouter

from .views import CanteenViewSet, CategoryViewSet, DishViewSet

router = DefaultRouter()
router.register('canteens', CanteenViewSet)
router.register('categories', CategoryViewSet)
router.register('dishes', DishViewSet, basename='dish')

urlpatterns = router.urls
