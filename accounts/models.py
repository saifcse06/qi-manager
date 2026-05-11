from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model that extends AbstractUser.
    Uses roles for RBAC instead of Django's default groups.
    """
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    # Many-to-many relationship with Role
    roles = models.ManyToManyField('Role', related_name='users', blank=True)
    # Override related_name for groups and user_permissions to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.roles.filter(name=role_name).exists()

    def has_permission(self, perm_codename):
        """
        Check if user has a specific permission through their roles.
        perm_codename format: 'app_label.action_model' (e.g., 'accounts.view_user')
        """
        if self.is_superuser:
            return True
        return self.roles.filter(permissions__codename=perm_codename).exists()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Role(models.Model):
    """
    Role model for RBAC.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Many-to-many relationship with Permission
    permissions = models.ManyToManyField('Permission', related_name='roles', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'


class Permission(models.Model):
    """
    Permission model for RBAC.
    """
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100, unique=True)  # Format: 'app.action_model'
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.codename})"

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['codename']