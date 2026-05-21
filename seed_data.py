#!/usr/bin/env python
"""
Seed script to populate the database with sample RBAC data.
Run with: venv/bin/python seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/mdsaifuddin/Desktop/SaifDev/QI-Management/Development/qi-manager')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Role, Permission

User = get_user_model()

def create_permissions():
    """Create sample permissions for the RBAC system."""
    permissions_data = [
        # User permissions
        {'name': 'Can view user', 'codename': 'accounts.view_user', 'description': 'Can view user'},
        {'name': 'Can add user', 'codename': 'accounts.add_user', 'description': 'Can add user'},
        {'name': 'Can change user', 'codename': 'accounts.change_user', 'description': 'Can change user'},
        {'name': 'Can delete user', 'codename': 'accounts.delete_user', 'description': 'Can delete user'},
        # Role permissions
        {'name': 'Can view role', 'codename': 'accounts.view_role', 'description': 'Can view role'},
        {'name': 'Can add role', 'codename': 'accounts.add_role', 'description': 'Can add role'},
        {'name': 'Can change role', 'codename': 'accounts.change_role', 'description': 'Can change role'},
        {'name': 'Can delete role', 'codename': 'accounts.delete_role', 'description': 'Can delete role'},
        # Permission permissions
        {'name': 'Can view permission', 'codename': 'accounts.view_permission', 'description': 'Can view permission'},
        {'name': 'Can add permission', 'codename': 'accounts.add_permission', 'description': 'Can add permission'},
        {'name': 'Can change permission', 'codename': 'accounts.change_permission', 'description': 'Can change permission'},
        {'name': 'Can delete permission', 'codename': 'accounts.delete_permission', 'description': 'Can delete permission'},
        # Dashboard / Home
        {'name': 'Can view dashboard', 'codename': 'accounts.view_dashboard', 'description': 'Can view dashboard'},
        {'name': 'Can view profile', 'codename': 'accounts.view_profile', 'description': 'Can view profile'},
        # System Settings permissions
        {'name': 'Can view settings', 'codename': 'settings_app.view_settings', 'description': 'Can view system settings'},
        {'name': 'Can change settings', 'codename': 'settings_app.change_settings', 'description': 'Can change system settings'},
        {'name': 'Can delete payment method', 'codename': 'settings_app.delete_paymentmethod', 'description': 'Can delete payment method'},
        {'name': 'Can delete payment term', 'codename': 'settings_app.delete_paymentterm', 'description': 'Can delete payment term'},
        # Client Management permissions
        {'name': 'Can view clients', 'codename': 'clients.view_client', 'description': 'Can view clients'},
        {'name': 'Can add client', 'codename': 'clients.add_client', 'description': 'Can add client'},
        {'name': 'Can change client', 'codename': 'clients.change_client', 'description': 'Can change client'},
        {'name': 'Can delete client', 'codename': 'clients.delete_client', 'description': 'Can delete client'},
        {'name': 'Can view contact person', 'codename': 'clients.view_clientcontactperson', 'description': 'Can view contact person'},
        {'name': 'Can add contact person', 'codename': 'clients.add_clientcontactperson', 'description': 'Can add contact person'},
        {'name': 'Can change contact person', 'codename': 'clients.change_clientcontactperson', 'description': 'Can change contact person'},
        {'name': 'Can delete contact person', 'codename': 'clients.delete_clientcontactperson', 'description': 'Can delete contact person'},
    ]

    created = []
    for perm_data in permissions_data:
        perm, created_flag = Permission.objects.get_or_create(
            codename=perm_data['codename'],
            defaults={
                'name': perm_data['name'],
                'description': perm_data['description'],
            }
        )
        if created_flag:
            created.append(perm)

    print(f"Created {len(created)} permissions")
    return Permission.objects.all()


def create_roles(all_permissions):
    """Create sample roles with appropriate permissions."""
    # Super Admin - all permissions
    super_admin, created = Role.objects.get_or_create(
        name='Super Admin',
        defaults={
            'description': 'Super Administrator with all permissions',
        }
    )
    if created:
        super_admin.permissions.set(all_permissions)
        print(f"Created role: {super_admin.name} with {all_permissions.count()} permissions")
    else:
        super_admin.permissions.set(all_permissions)
        print(f"Updated role: {super_admin.name} with {all_permissions.count()} permissions")

    # Admin - user, role, settings, and client management
    admin_perms = all_permissions.filter(
        codename__in=[
            'accounts.view_user', 'accounts.add_user', 'accounts.change_user',
            'accounts.view_role', 'accounts.add_role', 'accounts.change_role',
            'accounts.view_permission',
            'accounts.view_dashboard', 'accounts.view_profile',
            'settings_app.view_settings', 'settings_app.change_settings',
            'settings_app.delete_paymentmethod', 'settings_app.delete_paymentterm',
            'clients.view_client', 'clients.add_client', 'clients.change_client',
            'clients.view_clientcontactperson', 'clients.add_clientcontactperson',
            'clients.change_clientcontactperson',
        ]
    )
    admin_role, created = Role.objects.get_or_create(
        name='Admin',
        defaults={
            'description': 'Administrator with user, role, settings, and client management permissions',
        }
    )
    if created:
        admin_role.permissions.set(admin_perms)
        print(f"Created role: {admin_role.name} with {admin_perms.count()} permissions")
    else:
        admin_role.permissions.set(admin_perms)
        print(f"Updated role: {admin_role.name} with {admin_perms.count()} permissions")

    # Manager - view only (including clients)
    manager_perms = all_permissions.filter(
        codename__in=[
            'accounts.view_user',
            'accounts.view_role',
            'accounts.view_permission',
            'accounts.view_dashboard', 'accounts.view_profile',
            'clients.view_client',
            'clients.view_clientcontactperson',
        ]
    )
    manager_role, created = Role.objects.get_or_create(
        name='Manager',
        defaults={
            'description': 'Manager with view-only permissions',
        }
    )
    if created:
        manager_role.permissions.set(manager_perms)
        print(f"Created role: {manager_role.name} with {manager_perms.count()} permissions")
    else:
        manager_role.permissions.set(manager_perms)
        print(f"Updated role: {manager_role.name} with {manager_perms.count()} permissions")

    # Additional roles without special permissions
    for role_name in ['Technician', 'Accountant', 'Sales Executive']:
        role, created = Role.objects.get_or_create(
            name=role_name,
            defaults={
                'description': f'{role_name} role',
            }
        )
        if created:
            print(f"Created role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")


def create_admin_user(super_admin_role):
    """Create default admin user if not exists."""
    try:
        user = User.objects.get(username='admin')
        print(f"Admin user already exists: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        print(f"Created admin user: {user.username}")

    # Assign Super Admin role
    user.roles.add(super_admin_role)
    print(f"Assigned '{super_admin_role.name}' role to admin user")


def main():
    print("=" * 50)
    print("Seeding RBAC Data")
    print("=" * 50)

    print("\n[1/3] Creating permissions...")
    all_permissions = create_permissions()

    print("\n[2/3] Creating roles with permissions...")
    create_roles(all_permissions)

    print("\n[3/3] Creating admin user...")
    super_admin_role = Role.objects.get(name='Super Admin')
    create_admin_user(super_admin_role)

    print("\n" + "=" * 50)
    print("Seed data created successfully!")
    print("=" * 50)

    # Summary
    print("\nSummary:")
    print(f"  Users: {User.objects.count()}")
    print(f"  Roles: {Role.objects.count()}")
    print(f"  Permissions: {Permission.objects.count()}")


if __name__ == '__main__':
    main()
