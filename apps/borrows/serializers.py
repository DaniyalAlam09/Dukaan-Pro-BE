from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.borrows.models import Borrow, BorrowItem
from apps.inventory.models import Product


class BorrowItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity_borrowed = serializers.DecimalField(max_digits=12, decimal_places=2)


class BorrowItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    quantity_pending = serializers.SerializerMethodField()
    item_status = serializers.SerializerMethodField()

    class Meta:
        model = BorrowItem
        fields = (
            "id",
            "product",
            "product_name",
            "unit",
            "quantity_borrowed",
            "quantity_returned",
            "quantity_pending",
            "item_status",
        )
        read_only_fields = (
            "id",
            "product_name",
            "unit",
            "quantity_pending",
            "item_status",
        )

    def get_quantity_pending(self, obj: BorrowItem):
        return f"{(obj.quantity_pending or 0):.2f}"

    def get_item_status(self, obj: BorrowItem):
        return "returned" if (obj.quantity_pending or 0) <= 0 else "open"


class BorrowSerializer(serializers.ModelSerializer):
    items = BorrowItemSerializer(many=True, read_only=True)
    items_payload = BorrowItemWriteSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = Borrow
        fields = (
            "id",
            "direction",
            "party",
            "borrow_date",
            "expected_return_date",
            "status",
            "notes",
            "created_at",
            "items",
            "items_payload",
        )
        read_only_fields = ("id", "status", "created_at", "items")

    def validate_items_payload(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        items_payload = validated_data.pop("items_payload")

        borrow = Borrow.objects.create(user=user, **validated_data)

        for item in items_payload:
            product = item["product"]
            if product.user_id != user.id:
                raise serializers.ValidationError("Invalid product.")
            qty = item["quantity_borrowed"]
            BorrowItem.objects.create(borrow=borrow, product=product, quantity_borrowed=qty)

            # stock adjustment at creation
            if borrow.direction == Borrow.DIR_LENT_OUT:
                product.current_stock = (product.current_stock or 0) - qty
            else:
                product.current_stock = (product.current_stock or 0) + qty
            product.save(update_fields=["current_stock", "updated_at"])

        borrow.status = borrow.recompute_status()
        borrow.save(update_fields=["status"])
        return borrow

    @transaction.atomic
    def update(self, instance: Borrow, validated_data):
        # Minimal MVP: only allow updating metadata while open.
        if instance.status != Borrow.STATUS_OPEN:
            raise serializers.ValidationError("Only open borrows can be updated.")

        items_payload = validated_data.pop("items_payload", None)
        if items_payload is not None:
            raise serializers.ValidationError("Updating items is not supported; create a new borrow instead.")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RecordReturnLineSerializer(serializers.Serializer):
    borrow_item_id = serializers.IntegerField()
    quantity_returned = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_quantity_returned(self, v):
        if v <= 0:
            raise serializers.ValidationError("Quantity returned must be > 0.")
        return v

