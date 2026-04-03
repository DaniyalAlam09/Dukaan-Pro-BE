from rest_framework.routers import DefaultRouter

from apps.parties.views import PartyViewSet

router = DefaultRouter()
router.register(r"parties", PartyViewSet, basename="parties")

urlpatterns = router.urls

