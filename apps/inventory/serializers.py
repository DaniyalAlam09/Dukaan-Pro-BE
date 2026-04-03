from rest_framework import serializers

from apps.inventory.models import Product, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ("id", "name")
        read_only_fields = ("id",)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
            "category_name",
            "unit",
            "buying_price",
            "retail_price",
            "wholesale_price",
            "current_stock",
            "low_stock_threshold",
            "is_low_stock",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "category_name", "is_low_stock")

    def get_is_low_stock(self, obj: Product) -> bool:
        try:
            return obj.current_stock <= obj.low_stock_threshold
        except Exception:
            return False

