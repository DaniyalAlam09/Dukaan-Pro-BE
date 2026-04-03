from rest_framework.routers import DefaultRouter

from apps.purchases.views import PurchaseViewSet

router = DefaultRouter()
router.register(r"purchases", PurchaseViewSet, basename="purchases")

urlpatterns = router.urls

