from datetime import date
from decimal import Decimal

from django.db.models import F, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.borrows.models import Borrow
from apps.inventory.models import Product
from apps.purchases.models import Purchase
from apps.sales.models import Sale


class DashboardSummaryView(APIView):
    def get(self, request):
        today = date.today()

        today_sales = (
            Sale.objects.filter(user=request.user, sale_date=today).aggregate(s=Sum("total_amount"))["s"]
            or Decimal("0")
        )
        today_purchases = (
            Purchase.objects.filter(user=request.user, purchase_date=today).aggregate(s=Sum("total_amount"))["s"]
            or Decimal("0")
        )

        # Receivable/payable: sum of unpaid balances
        sales_unpaid = (
            Sale.objects.filter(user=request.user)
            .aggregate(s=Sum(F("total_amount") - F("amount_paid")))["s"]
            or Decimal("0")
        )
        purchases_unpaid = (
            Purchase.objects.filter(user=request.user)
            .aggregate(s=Sum(F("total_amount") - F("amount_paid")))["s"]
            or Decimal("0")
        )

        low_stock_qs = Product.objects.filter(
            user=request.user, current_stock__lte=F("low_stock_threshold")
        ).order_by("current_stock")[:10]
        low_stock_products = [
            {
                "id": p.id,
                "name": p.name,
                "current_stock": f"{p.current_stock:.2f}",
                "low_stock_threshold": f"{p.low_stock_threshold:.2f}",
                "unit": p.unit,
            }
            for p in low_stock_qs
        ]

        open_lent = Borrow.objects.filter(
            user=request.user,
            direction=Borrow.DIR_LENT_OUT,
        ).exclude(status=Borrow.STATUS_RETURNED).count()
        open_borrowed = Borrow.objects.filter(
            user=request.user,
            direction=Borrow.DIR_BORROWED_IN,
        ).exclude(status=Borrow.STATUS_RETURNED).count()

        recent_sales_qs = Sale.objects.filter(user=request.user).order_by("-sale_date", "-id")[:5]
        recent_sales = [
            {
                "id": s.id,
                "sale_date": str(s.sale_date),
                "party_id": s.party_id,
                "total_amount": f"{s.total_amount:.2f}",
                "amount_paid": f"{s.amount_paid:.2f}",
                "payment_status": s.payment_status,
            }
            for s in recent_sales_qs
        ]

        recent_purchases_qs = Purchase.objects.filter(user=request.user).order_by("-purchase_date", "-id")[:5]
        recent_purchases = [
            {
                "id": p.id,
                "purchase_date": str(p.purchase_date),
                "party_id": p.party_id,
                "total_amount": f"{p.total_amount:.2f}",
                "amount_paid": f"{p.amount_paid:.2f}",
                "payment_status": p.payment_status,
            }
            for p in recent_purchases_qs
        ]

        return Response(
            {
                "today_sales": float(today_sales),
                "today_purchases": float(today_purchases),
                "total_receivable": float(sales_unpaid),
                "total_payable": float(purchases_unpaid),
                "low_stock_products": low_stock_products,
                "open_borrows_lent_out": open_lent,
                "open_borrows_borrowed_in": open_borrowed,
                "recent_sales": recent_sales,
                "recent_purchases": recent_purchases,
            }
        )

