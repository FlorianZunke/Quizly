from rest_framework.permissions import BasePermission, SAFE_METHODS



class IsOwner(BasePermission):
    """
    Custom permission to only allow the owner of an object to access it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user