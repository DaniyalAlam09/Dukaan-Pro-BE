from rest_framework import viewsets

from apps.inventory.models import Product, ProductCategory
from apps.inventory.serializers import ProductCategorySerializer, ProductSerializer
from utils.permissions import IsOwner


class UserScopedQuerysetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductCategoryViewSet(UserScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsOwner]
    queryset = ProductCategory.objects.all()
    search_fields = ("name",)
    ordering_fields = ("name", "id")


class ProductViewSet(UserScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsOwner]
    queryset = Product.objects.select_related("category").all()
    filterset_fields = ("category", "unit")
    search_fields = ("name",)
    ordering_fields = ("updated_at", "created_at", "name", "current_stock", "id")

from django.shortcuts import render

# Create your views here.
