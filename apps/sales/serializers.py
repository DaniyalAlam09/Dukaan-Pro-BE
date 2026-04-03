from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Product
from apps.sales.models import Sale, SaleItem


class SaleItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)

    class Meta:
        model = SaleItem
        fields = ("id", "product", "product_name", "unit", "quantity", "unit_price", "subtotal")
        read_only_fields = ("id", "subtotal", "product_name", "unit")


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    items_payload = SaleItemWriteSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = Sale
        fields = (
            "id",
            "party",
            "sale_type",
            "sale_date",
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

        sale = Sale.objects.create(user=user, **validated_data)

        total = Decimal("0")
        for item in items_payload:
            product = item["product"]
            if product.user_id != user.id:
                raise serializers.ValidationError("Invalid product.")
            qty = item["quantity"]
            unit_price = item["unit_price"]
            SaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=unit_price)
            # stock deduction
            product.current_stock = (product.current_stock or 0) - qty
            product.save(update_fields=["current_stock", "updated_at"])
            total += qty * unit_price

        sale.total_amount = total
        sale.payment_status = sale.compute_payment_status()
        sale.save(update_fields=["total_amount", "payment_status"])

        # auto-create payment record if amount_paid > 0
        amount_paid = sale.amount_paid or 0
        if amount_paid > 0:
            from apps.payments.models import Payment

            Payment.objects.create(
                user=user,
                party=sale.party,
                payment_type=Payment.TYPE_RECEIVED,
                amount=amount_paid,
                payment_date=sale.sale_date,
                note="Auto from sale",
                related_sale=sale,
            )

        return sale

    @transaction.atomic
    def update(self, instance: Sale, validated_data):
        """
        MVP approach: if items_payload is provided, replace items and reverse stock accordingly.
        """
        user = self.context["request"].user
        items_payload = validated_data.pop("items_payload", None)

        # handle stock reversal if replacing items
        if items_payload is not None:
            # reverse existing stock deduction
            for old_item in instance.items.select_related("product").all():
                p = old_item.product
                p.current_stock = (p.current_stock or 0) + (old_item.quantity or 0)
                p.save(update_fields=["current_stock", "updated_at"])
            instance.items.all().delete()

            total = Decimal("0")
            for item in items_payload:
                product = item["product"]
                if product.user_id != user.id:
                    raise serializers.ValidationError("Invalid product.")
                qty = item["quantity"]
                unit_price = item["unit_price"]
                SaleItem.objects.create(
                    sale=instance, product=product, quantity=qty, unit_price=unit_price
                )
                product.current_stock = (product.current_stock or 0) - qty
                product.save(update_fields=["current_stock", "updated_at"])
                total += qty * unit_price
            instance.total_amount = total

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.payment_status = instance.compute_payment_status()
        instance.save()
        return instance

