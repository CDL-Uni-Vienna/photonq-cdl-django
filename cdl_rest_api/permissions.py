from rest_framework import permissions


class UpdateOwnProfile(permissions.BasePermission):
    """Allow user to edit their own profile"""

    # Has_object_permission gets called every time a request is made
    # to the API that we assign our permission to
    # has_object_permission function defines permission class
    def has_object_permission(self, request, view, obj):
        """Check if user is trying to edit their own profile"""

        return obj.id == request.user.id


class OriginAuthenticated(permissions.BasePermission):
    """Allow only authenticated users to access the API"""

    def has_permission(self, request, view):
        print("origin user", request.origin_user)
        """Check if user is authenticated"""
        return request.origin_user
