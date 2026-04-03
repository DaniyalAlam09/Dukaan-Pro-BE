from django.conf import settings
from django.db import models

from apps.parties.models import Party


class Payment(models.Model):
    TYPE_RECEIVED = "received"
    TYPE_SENT = "sent"
    PAYMENT_TYPE_CHOICES = (
        (TYPE_RECEIVED, "Received"),
        (TYPE_SENT, "Sent"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="payments")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    note = models.TextField(blank=True, default="")

    related_sale = models.ForeignKey(
        "sales.Sale", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    related_purchase = models.ForeignKey(
        "purchases.Purchase", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-payment_date", "-id")

    def __str__(self):
        return f"Payment {self.id}"
