from rest_framework import serializers

from apps.parties.models import Party


class PartySerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Party
        fields = (
            "id",
            "name",
            "phone",
            "address",
            "party_type",
            "created_at",
            "balance",
        )
        read_only_fields = ("id", "created_at", "balance")

