from rest_framework.routers import DefaultRouter

from apps.inventory.views import ProductCategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"product-categories", ProductCategoryViewSet, basename="product-categories")

urlpatterns = router.urls

