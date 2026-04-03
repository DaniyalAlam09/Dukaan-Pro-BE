from django.conf import settings
from django.db import models


class ShopProfile(models.Model):
    SALE_TYPES_WHOLESALE = "wholesale"
    SALE_TYPES_RETAIL = "retail"
    SALE_TYPES_BOTH = "both"

    SALE_TYPES_CHOICES = (
        (SALE_TYPES_WHOLESALE, "Wholesale"),
        (SALE_TYPES_RETAIL, "Retail"),
        (SALE_TYPES_BOTH, "Both"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop_profile")
    shop_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, default="")
    sale_types = models.CharField(max_length=20, choices=SALE_TYPES_CHOICES, default=SALE_TYPES_BOTH)
    currency = models.CharField(max_length=8, default="PKR")
    city = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop_name} ({self.user_id})"
