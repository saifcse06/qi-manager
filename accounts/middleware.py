import re
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


class RoleMiddleware:
    """
    Middleware to check role-based access control for URLs.
    Checks if the user has the required role(s) to access a URL.
    Superusers bypass all checks.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Define role requirements for URL patterns
        self.role_required_by_url = getattr(settings, 'MIDDLEWARE_ROLE_MAP', {
            r'^/users/': ['Super Admin', 'Admin'],
            r'^/roles/': ['Super Admin', 'Admin'],
            r'^/permissions/': ['Super Admin'],
        })
        # URLs that are exempt from role checking
        self.exempt_urls = getattr(settings, 'MIDDLEWARE_EXEMPT_URLS', [
            r'^/admin/',
            r'^/login/',
            r'^/logout/',
            r'^/password_reset/',
            r'^/social-auth/',
            r'^/static/',
            r'^/media/',
            r'^/home/',
            r'^/profile/',
            r'^/accounts/',  # allauth URLs (Google OAuth, etc.)
        ])

    def __call__(self, request):
        path = request.path_info

        # Check if URL is exempt
        if any(re.match(pattern, path) for pattern in self.exempt_urls):
            return self.get_response(request)

        # If user is not authenticated, redirect to login
        if not request.user.is_authenticated:
            return redirect('login')

        # Superuser bypasses all role checks
        if request.user.is_superuser:
            return self.get_response(request)

        # Check role requirements for the current URL
        required_roles = None
        for pattern, roles in self.role_required_by_url.items():
            if re.match(pattern, path):
                required_roles = roles
                break

        # If no specific role required, allow access
        if required_roles is None:
            return self.get_response(request)

        # Check if user has any of the required roles
        user_roles = list(request.user.roles.values_list('name', flat=True))
        if not set(required_roles).intersection(set(user_roles)):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('home')

        return self.get_response(request)