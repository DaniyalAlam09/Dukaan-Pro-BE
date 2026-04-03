from rest_framework import generics

from apps.shop.models import ShopProfile
from apps.shop.serializers import ShopProfileSerializer


class ShopProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ShopProfileSerializer

    def get_object(self):
        profile, _ = ShopProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "shop_name": f"{self.request.user.full_name}'s Shop",
                "category": "",
                "sale_types": ShopProfile.SALE_TYPES_BOTH,
                "currency": "PKR",
                "city": "",
            },
        )
        return profile

    def put(self, request, *args, **kwargs):
        # Ensure full update semantics
        return super().put(request, *args, **kwargs)
