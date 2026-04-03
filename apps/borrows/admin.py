from django.contrib import admin
from apps.borrows.models import Borrow, BorrowItem

admin.site.register(Borrow)
admin.site.register(BorrowItem)
