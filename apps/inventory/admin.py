from django.contrib import admin
from apps.inventory.models import Product, ProductCategory

admin.site.register(ProductCategory)
admin.site.register(Product)
