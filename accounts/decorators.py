from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from functools import wraps


def role_required(*roles):
    """
    Decorator for views that checks if the user has any of the specified roles.
    Superuser bypasses the check.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not roles:
                return view_func(request, *args, **kwargs)
            
            user_roles = request.user.roles.values_list('name', flat=True)
            if not set(roles).intersection(set(user_roles)):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def permission_required(permission):
    """
    Decorator for views that checks if the user has the specified permission.
    Permission format: 'app_label.action_model' (e.g., 'accounts.view_user')
    Superuser bypasses the check.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not request.user.has_permission(permission):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator