from django import template
from django.contrib.auth.models import Permission

register = template.Library()

@register.filter
def has_role(user, role_name):
    """Check if user has a specific role"""
    if user.is_authenticated:
        return user.roles.filter(name=role_name).exists()
    return False

@register.filter
def has_permission(user, perm_codename):
    """Check if user has a specific permission"""
    if user.is_authenticated:
        return user.has_permission(perm_codename)
    return False

@register.filter
def has_any_role(user, role_names):
    """Check if user has any of the specified roles (comma-separated)"""
    if not user.is_authenticated:
        return False
    
    role_list = [r.strip() for r in role_names.split(',')]
    user_roles = user.roles.values_list('name', flat=True)
    return any(role in user_roles for role in role_list)

@register.simple_tag
def get_user_roles(user):
    """Get all roles for a user"""
    if user.is_authenticated:
        return user.roles.all()
    return []

@register.simple_tag
def get_role_permissions(role):
    """Get all permissions for a role"""
    if role:
        return role.permissions.all()
    return []