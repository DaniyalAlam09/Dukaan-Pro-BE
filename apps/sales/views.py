from django.db import transaction
from rest_framework import viewsets

from apps.sales.models import Sale
from apps.sales.serializers import SaleSerializer
from utils.permissions import IsOwner


class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsOwner]
    queryset = Sale.objects.prefetch_related("items").all()
    filterset_fields = ("party", "payment_status", "sale_type")
    ordering_fields = ("sale_date", "total_amount", "id")
    search_fields = ("notes",)

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(sale_date__gte=start)
        if end:
            qs = qs.filter(sale_date__lte=end)
        party = self.request.query_params.get("party")
        if party:
            qs = qs.filter(party_id=party)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(payment_status=status)
        return qs

    @transaction.atomic
    def perform_destroy(self, instance: Sale):
        # reverse stock deduction
        for item in instance.items.select_related("product").all():
            p = item.product
            p.current_stock = (p.current_stock or 0) + (item.quantity or 0)
            p.save(update_fields=["current_stock", "updated_at"])
        instance.delete()
