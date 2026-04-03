from django.urls import path

from apps.shop.reports_views import (
    PartyBalancesReportView,
    SalesSummaryReportView,
    TopProductsReportView,
)

urlpatterns = [
    path("reports/sales-summary/", SalesSummaryReportView.as_view(), name="reports-sales-summary"),
    path("reports/party-balances/", PartyBalancesReportView.as_view(), name="reports-party-balances"),
    path("reports/top-products/", TopProductsReportView.as_view(), name="reports-top-products"),
]

