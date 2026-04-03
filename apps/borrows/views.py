from django.db import transaction
from rest_framework import decorators, exceptions, response, status, viewsets

from apps.borrows.models import Borrow, BorrowItem
from apps.borrows.serializers import BorrowSerializer, RecordReturnLineSerializer
from utils.permissions import IsOwner


class BorrowViewSet(viewsets.ModelViewSet):
    serializer_class = BorrowSerializer
    permission_classes = [IsOwner]
    queryset = Borrow.objects.prefetch_related("items").all()
    filterset_fields = ("direction", "status", "party")
    ordering_fields = ("borrow_date", "created_at", "id")
    search_fields = ("notes",)

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        direction = self.request.query_params.get("direction")
        if direction in {Borrow.DIR_LENT_OUT, Borrow.DIR_BORROWED_IN}:
            qs = qs.filter(direction=direction)
        status_q = self.request.query_params.get("status")
        if status_q in {Borrow.STATUS_OPEN, Borrow.STATUS_PARTIALLY_RETURNED, Borrow.STATUS_RETURNED}:
            qs = qs.filter(status=status_q)
        party = self.request.query_params.get("party")
        if party:
            qs = qs.filter(party_id=party)
        return qs

    @transaction.atomic
    def perform_destroy(self, instance: Borrow):
        # Rule: only allow delete if open; reverse initial stock change
        if instance.status != Borrow.STATUS_OPEN:
            raise exceptions.ValidationError("Cannot delete a borrow that has returns.")

        for item in instance.items.select_related("product").all():
            p = item.product
            qty = item.quantity_borrowed or 0
            if instance.direction == Borrow.DIR_LENT_OUT:
                p.current_stock = (p.current_stock or 0) + qty
            else:
                p.current_stock = (p.current_stock or 0) - qty
            p.save(update_fields=["current_stock", "updated_at"])
        instance.delete()

    @decorators.action(detail=True, methods=["post"], url_path="record-return")
    @transaction.atomic
    def record_return(self, request, pk=None):
        borrow: Borrow = self.get_object()
        lines = RecordReturnLineSerializer(data=request.data, many=True)
        lines.is_valid(raise_exception=True)

        # map items by id
        items = {i.id: i for i in BorrowItem.objects.select_related("product").filter(borrow=borrow)}

        for line in lines.validated_data:
            item_id = line["borrow_item_id"]
            qty = line["quantity_returned"]
            if item_id not in items:
                return response.Response(
                    {"detail": f"Invalid borrow_item_id {item_id}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item = items[item_id]
            pending = item.quantity_pending or 0
            if qty > pending:
                return response.Response(
                    {"detail": f"Return qty exceeds pending for item {item_id}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # apply return + adjust stock
            item.quantity_returned = (item.quantity_returned or 0) + qty
            item.save(update_fields=["quantity_returned"])

            p = item.product
            if borrow.direction == Borrow.DIR_LENT_OUT:
                # items came back to shelf
                p.current_stock = (p.current_stock or 0) + qty
            else:
                # returning items to lender means leaving shelf
                p.current_stock = (p.current_stock or 0) - qty
            p.save(update_fields=["current_stock", "updated_at"])

        borrow.status = borrow.recompute_status()
        borrow.save(update_fields=["status"])
        # Ensure fresh related data after updates
        borrow.refresh_from_db()
        return response.Response(BorrowSerializer(borrow, context={"request": request}).data)
