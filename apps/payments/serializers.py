from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "party",
            "payment_type",
            "amount",
            "payment_date",
            "note",
            "related_sale",
            "related_purchase",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "related_sale", "related_purchase")

