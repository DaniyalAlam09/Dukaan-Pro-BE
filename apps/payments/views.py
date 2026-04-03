from rest_framework import viewsets

from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from utils.permissions import IsOwner


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsOwner]
    queryset = Payment.objects.all()
    filterset_fields = ("party", "payment_type")
    ordering_fields = ("payment_date", "amount", "id")
    search_fields = ("note",)

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        party = self.request.query_params.get("party")
        if party:
            qs = qs.filter(party_id=party)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
