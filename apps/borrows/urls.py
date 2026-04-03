from rest_framework.routers import DefaultRouter

from apps.borrows.views import BorrowViewSet

router = DefaultRouter()
router.register(r"borrows", BorrowViewSet, basename="borrows")

urlpatterns = router.urls

