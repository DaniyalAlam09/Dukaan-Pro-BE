from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.parties.models import Party
from apps.sales.models import Sale, SaleItem


class SalesSummaryReportView(APIView):
    def get(self, request):
        period = request.query_params.get("period", "daily")
        if period not in {"daily", "weekly", "monthly"}:
            raise ValidationError("period must be daily|weekly|monthly")

        # last 30 buckets-ish
        if period == "daily":
            trunc = TruncDay("sale_date")
            start = date.today() - timedelta(days=29)
        elif period == "weekly":
            trunc = TruncWeek("sale_date")
            start = date.today() - timedelta(weeks=11)
        else:
            trunc = TruncMonth("sale_date")
            start = date.today().replace(day=1) - timedelta(days=365)

        qs = (
            Sale.objects.filter(user=request.user, sale_date__gte=start)
            .annotate(bucket=trunc)
            .values("bucket")
            .annotate(total=Sum("total_amount"), count=Count("id"))
            .order_by("bucket")
        )

        data = [
            {"date": str(r["bucket"].date() if hasattr(r["bucket"], "date") else r["bucket"]), "total": float(r["total"] or 0), "count": r["count"]}
            for r in qs
        ]
        return Response({"period": period, "series": data})


class PartyBalancesReportView(APIView):
    def get(self, request):
        party_type = request.query_params.get("type", "customer")
        if party_type not in {"customer", "supplier"}:
            raise ValidationError("type must be customer|supplier")

        qs = Party.objects.filter(user=request.user)
        if party_type == "customer":
            qs = qs.filter(party_type__in=[Party.TYPE_CUSTOMER, Party.TYPE_BOTH])
        else:
            qs = qs.filter(party_type__in=[Party.TYPE_SUPPLIER, Party.TYPE_BOTH])

        # compute via same rule as ledger balance
        from apps.parties.views import compute_party_balance

        rows = []
        for p in qs.order_by("name").only("id", "name"):
            rows.append({"party_id": p.id, "name": p.name, "balance": float(compute_party_balance(request.user, p.id))})
        return Response({"type": party_type, "rows": rows})


class TopProductsReportView(APIView):
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        limit = max(1, min(limit, 50))

        # Top products by quantity sold (sales items)
        qs = (
            SaleItem.objects.filter(sale__user=request.user)
            .values("product_id", "product__name", "product__unit")
            .annotate(quantity=Sum("quantity"), revenue=Sum("subtotal"))
            .order_by("-quantity")[:limit]
        )
        rows = [
            {
                "product_id": r["product_id"],
                "name": r["product__name"],
                "unit": r["product__unit"],
                "quantity": float(r["quantity"] or 0),
                "revenue": float(r["revenue"] or 0),
            }
            for r in qs
        ]
        return Response({"limit": limit, "rows": rows})

