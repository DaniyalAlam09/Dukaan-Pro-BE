from django.conf import settings
from django.db import models


class Party(models.Model):
    TYPE_CUSTOMER = "customer"
    TYPE_SUPPLIER = "supplier"
    TYPE_BOTH = "both"

    PARTY_TYPE_CHOICES = (
        (TYPE_CUSTOMER, "Customer"),
        (TYPE_SUPPLIER, "Supplier"),
        (TYPE_BOTH, "Both"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="parties")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES, default=TYPE_CUSTOMER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name", "id")

    def __str__(self):
        return self.name

