from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.authentication.models import User
from apps.shop.models import ShopProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "created_at")
        read_only_fields = ("id", "created_at")


class ShopProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopProfile
        fields = (
            "shop_name",
            "category",
            "sale_types",
            "currency",
            "city",
            "created_at",
        )
        read_only_fields = ("created_at",)


class SignupSerializer(serializers.Serializer):
    # Step 1
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    # Step 2
    shop_name = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=255, required=False, allow_blank=True)
    sale_types = serializers.ChoiceField(
        choices=ShopProfile.SALE_TYPES_CHOICES, default=ShopProfile.SALE_TYPES_BOTH
    )
    currency = serializers.CharField(max_length=8, default="PKR")
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )
        ShopProfile.objects.create(
            user=user,
            shop_name=validated_data["shop_name"],
            category=validated_data.get("category", ""),
            sale_types=validated_data.get("sale_types", ShopProfile.SALE_TYPES_BOTH),
            currency=validated_data.get("currency", "PKR"),
            city=validated_data.get("city", ""),
        )
        return user


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "phone")


class ShopDashTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adds user + shop profile to the token response.
    """

    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        # Ensure email/password auth works with custom user model
        authenticate_kwargs = {
            self.username_field: attrs.get(self.username_field),
            "password": attrs.get("password"),
        }
        user = authenticate(**authenticate_kwargs)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        shop = getattr(self.user, "shop_profile", None)
        data["shop_profile"] = ShopProfileSerializer(shop).data if shop else None
        return data

