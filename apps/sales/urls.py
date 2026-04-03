from rest_framework.routers import DefaultRouter

from apps.sales.views import SaleViewSet

router = DefaultRouter()
router.register(r"sales", SaleViewSet, basename="sales")

urlpatterns = router.urls

