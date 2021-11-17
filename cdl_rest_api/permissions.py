from rest_framework import permissions


class UpdateOwnProfile(permissions.BasePermission):
    """Allow user to edit their own profile"""

    # Has_object_permission gets called every time a request is made
    # to the API that we assign our permission to
    # has_object_permission function defines permission class
    def has_object_permission(self, request, obj):
        """Check if user is trying to edit their own profile"""
        # Allow users to view other users profiles but only able
        # to make changes to their own profile
        # Checks if the request is in the safe methods,
        # if it is, request is allowed to go through
        if request.method in permissions.SAFE_METHODS:
            return True
        # If it is not in the safe methods, the result of
        # the boolean expression is returned
        return obj.id == request.user.id
