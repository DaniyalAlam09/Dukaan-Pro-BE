from django.conf import settings
from django.db import models

from apps.inventory.models import Product
from apps.parties.models import Party


class Sale(models.Model):
    TYPE_WHOLESALE = "wholesale"
    TYPE_RETAIL = "retail"
    SALE_TYPE_CHOICES = (
        (TYPE_WHOLESALE, "Wholesale"),
        (TYPE_RETAIL, "Retail"),
    )

    STATUS_PAID = "paid"
    STATUS_PARTIAL = "partial"
    STATUS_CREDIT = "credit"
    PAYMENT_STATUS_CHOICES = (
        (STATUS_PAID, "Paid"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_CREDIT, "Credit"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sales")
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="sales")
    sale_type = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES, default=TYPE_RETAIL)
    sale_date = models.DateField()

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default=STATUS_CREDIT
    )
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-sale_date", "-id")

    def __str__(self):
        return f"Sale {self.id}"

    def compute_payment_status(self):
        if self.amount_paid <= 0:
            return self.STATUS_CREDIT
        if self.amount_paid < self.total_amount:
            return self.STATUS_PARTIAL
        return self.STATUS_PAID


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)

