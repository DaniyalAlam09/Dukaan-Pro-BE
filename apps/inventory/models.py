from django.conf import settings
from django.db import models


class ProductCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_categories")
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_METERS = "meters"
    UNIT_PIECES = "pieces"
    UNIT_DOZEN = "dozen"
    UNIT_KG = "kg"

    UNIT_CHOICES = (
        (UNIT_METERS, "Meters"),
        (UNIT_PIECES, "Pieces"),
        (UNIT_DOZEN, "Dozen"),
        (UNIT_KG, "Kg"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default=UNIT_PIECES)

    buying_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    low_stock_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")

    def __str__(self):
        return self.name

