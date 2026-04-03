from django.conf import settings
from django.db import models

from apps.inventory.models import Product
from apps.parties.models import Party


class Borrow(models.Model):
    DIR_LENT_OUT = "lent_out"
    DIR_BORROWED_IN = "borrowed_in"
    DIRECTION_CHOICES = (
        (DIR_LENT_OUT, "Lent Out"),
        (DIR_BORROWED_IN, "Borrowed In"),
    )

    STATUS_OPEN = "open"
    STATUS_PARTIALLY_RETURNED = "partially_returned"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_PARTIALLY_RETURNED, "Partially Returned"),
        (STATUS_RETURNED, "Returned"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrows")
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="borrows")
    borrow_date = models.DateField()
    expected_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-borrow_date", "-id")

    def __str__(self):
        return f"Borrow {self.id}"

    def recompute_status(self):
        # Avoid using prefetched/stale related manager cache.
        items = list(BorrowItem.objects.filter(borrow=self).only("quantity_borrowed", "quantity_returned"))
        if not items:
            return self.STATUS_OPEN
        any_returned = any((i.quantity_returned or 0) > 0 for i in items)
        all_returned = all((i.quantity_pending or 0) <= 0 for i in items)
        if all_returned:
            return self.STATUS_RETURNED
        if any_returned:
            return self.STATUS_PARTIALLY_RETURNED
        return self.STATUS_OPEN


class BorrowItem(models.Model):
    borrow = models.ForeignKey(Borrow, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="borrow_items")
    quantity_borrowed = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_returned = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ("id",)

    @property
    def quantity_pending(self):
        return (self.quantity_borrowed or 0) - (self.quantity_returned or 0)

