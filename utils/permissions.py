from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: only allow access to objects owned by request.user.
    Assumes the model has a `user` FK.
    """

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)

