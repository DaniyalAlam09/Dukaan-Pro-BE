from rest_framework import serializers

from apps.shop.models import ShopProfile


class ShopProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopProfile
        fields = (
            "shop_name",
            "category",
            "sale_types",
            "currency",
            "city",
            "created_at",
        )
        read_only_fields = ("created_at",)

