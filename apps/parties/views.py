from decimal import Decimal

from rest_framework import decorators, response, viewsets

from apps.parties.models import Party
from apps.parties.serializers import PartySerializer
from utils.permissions import IsOwner


def compute_party_balance(user, party_id) -> Decimal:
    from apps.payments.models import Payment
    from apps.purchases.models import Purchase
    from apps.sales.models import Sale

    receivable = (
        Sale.objects.filter(user=user, party_id=party_id)
        .values_list("total_amount", "amount_paid")
    )
    payable = (
        Purchase.objects.filter(user=user, party_id=party_id)
        .values_list("total_amount", "amount_paid")
    )

    bal = Decimal("0")
    for total, paid in receivable:
        bal += (total or 0) - (paid or 0)
    for total, paid in payable:
        bal -= (total or 0) - (paid or 0)

    for ptype, amount in Payment.objects.filter(user=user, party_id=party_id).values_list(
        "payment_type", "amount"
    ):
        if ptype == Payment.TYPE_RECEIVED:
            bal -= amount or 0
        else:
            bal += amount or 0
    return bal


class PartyViewSet(viewsets.ModelViewSet):
    serializer_class = PartySerializer
    permission_classes = [IsOwner]
    queryset = Party.objects.all()
    filterset_fields = ("party_type",)
    search_fields = ("name", "phone")
    ordering_fields = ("name", "created_at", "id")

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        party_type = self.request.query_params.get("type")
        if party_type in {Party.TYPE_CUSTOMER, Party.TYPE_SUPPLIER, Party.TYPE_BOTH}:
            if party_type == Party.TYPE_BOTH:
                return qs
            return qs.filter(party_type__in=[party_type, Party.TYPE_BOTH])
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        data = resp.data
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            for row in data["results"]:
                row["balance"] = f"{compute_party_balance(request.user, row['id']):.2f}"
        elif isinstance(data, list):
            for row in data:
                row["balance"] = f"{compute_party_balance(request.user, row['id']):.2f}"
        return resp

    def retrieve(self, request, *args, **kwargs):
        resp = super().retrieve(request, *args, **kwargs)
        resp.data["balance"] = f"{compute_party_balance(request.user, resp.data['id']):.2f}"
        return resp

    @decorators.action(detail=True, methods=["get"], url_path="ledger")
    def ledger(self, request, pk=None):
        from apps.payments.models import Payment
        from apps.purchases.models import Purchase
        from apps.sales.models import Sale

        party_id = int(pk)
        entries = []

        for s in Sale.objects.filter(user=request.user, party_id=party_id).values(
            "id", "sale_date", "total_amount", "amount_paid", "payment_status"
        ):
            unpaid = (s["total_amount"] or 0) - (s["amount_paid"] or 0)
            entries.append(
                {
                    "date": str(s["sale_date"]),
                    "type": "sale",
                    "ref_id": s["id"],
                    "amount": f"{unpaid:.2f}",
                }
            )

        for p in Purchase.objects.filter(user=request.user, party_id=party_id).values(
            "id", "purchase_date", "total_amount", "amount_paid", "payment_status"
        ):
            unpaid = (p["total_amount"] or 0) - (p["amount_paid"] or 0)
            entries.append(
                {
                    "date": str(p["purchase_date"]),
                    "type": "purchase",
                    "ref_id": p["id"],
                    "amount": f"{unpaid:.2f}",
                }
            )

        for pay in Payment.objects.filter(user=request.user, party_id=party_id).values(
            "id", "payment_date", "payment_type", "amount", "related_sale_id", "related_purchase_id"
        ):
            entries.append(
                {
                    "date": str(pay["payment_date"]),
                    "type": "payment_received" if pay["payment_type"] == Payment.TYPE_RECEIVED else "payment_sent",
                    "ref_id": pay["id"],
                    "amount": f"{(pay['amount'] or 0):.2f}",
                    "related_sale": pay["related_sale_id"],
                    "related_purchase": pay["related_purchase_id"],
                }
            )

        entries.sort(key=lambda e: (e["date"], e["type"], e["ref_id"]))

        running = Decimal("0")
        for e in entries:
            amt = Decimal(e["amount"])
            if e["type"] == "sale":
                running += amt
            elif e["type"] == "purchase":
                running -= amt
            elif e["type"] == "payment_received":
                running -= amt
            else:
                running += amt
            e["running_balance"] = f"{running:.2f}"

        return response.Response(
            {"party_id": party_id, "balance": f"{running:.2f}", "entries": entries}
        )
