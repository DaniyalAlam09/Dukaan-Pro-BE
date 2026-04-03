from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Product
from apps.purchases.models import Purchase, PurchaseItem


class PurchaseItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2)


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ("id", "product", "product_name", "unit", "quantity", "unit_cost", "subtotal")
        read_only_fields = ("id", "subtotal", "product_name", "unit")


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    items_payload = PurchaseItemWriteSerializer(many=True, write_only=True, required=True)

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        elif isinstance(data, dict):
            data = {**data}
        if isinstance(data, dict) and "items" in data and "items_payload" not in data:
            data["items_payload"] = data.pop("items")
        return super().to_internal_value(data)

    class Meta:
        model = Purchase
        fields = (
            "id",
            "party",
            "purchase_date",
            "total_amount",
            "amount_paid",
            "payment_status",
            "notes",
            "created_at",
            "items",
            "items_payload",
        )
        read_only_fields = ("id", "total_amount", "payment_status", "created_at", "items")

    def validate_items_payload(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_payload = validated_data.pop("items_payload")
        user = self.context["request"].user

        purchase = Purchase.objects.create(user=user, **validated_data)

        total = Decimal("0")
        for item in items_payload:
            product = item["product"]
            if product.user_id != user.id:
                raise serializers.ValidationError("Invalid product.")
            qty = item["quantity"]
            unit_cost = item["unit_cost"]
            PurchaseItem.objects.create(
                purchase=purchase, product=product, quantity=qty, unit_cost=unit_cost
            )
            # stock addition
            product.current_stock = (product.current_stock or 0) + qty
            product.save(update_fields=["current_stock", "updated_at"])
            total += qty * unit_cost

        purchase.total_amount = total
        purchase.payment_status = purchase.compute_payment_status()
        purchase.save(update_fields=["total_amount", "payment_status"])

        amount_paid = purchase.amount_paid or 0
        if amount_paid > 0:
            from apps.payments.models import Payment

            Payment.objects.create(
                user=user,
                party=purchase.party,
                payment_type=Payment.TYPE_SENT,
                amount=amount_paid,
                payment_date=purchase.purchase_date,
                note="Auto from purchase",
                related_purchase=purchase,
            )

        return purchase

    @transaction.atomic
    def update(self, instance: Purchase, validated_data):
        user = self.context["request"].user
        items_payload = validated_data.pop("items_payload", None)

        if items_payload is not None:
            # reverse existing stock addition
            for old_item in instance.items.select_related("product").all():
                p = old_item.product
                p.current_stock = (p.current_stock or 0) - (old_item.quantity or 0)
                p.save(update_fields=["current_stock", "updated_at"])
            instance.items.all().delete()

            total = Decimal("0")
            for item in items_payload:
                product = item["product"]
                if product.user_id != user.id:
                    raise serializers.ValidationError("Invalid product.")
                qty = item["quantity"]
                unit_cost = item["unit_cost"]
                PurchaseItem.objects.create(
                    purchase=instance, product=product, quantity=qty, unit_cost=unit_cost
                )
                product.current_stock = (product.current_stock or 0) + qty
                product.save(update_fields=["current_stock", "updated_at"])
                total += qty * unit_cost
            instance.total_amount = total

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.payment_status = instance.compute_payment_status()
        instance.save()
        return instance

