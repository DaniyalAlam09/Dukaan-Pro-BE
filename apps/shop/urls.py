from django.urls import path

from apps.shop.views import ShopProfileView

urlpatterns = [
    path("profile/", ShopProfileView.as_view(), name="shop-profile"),
]

