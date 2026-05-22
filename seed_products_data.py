#!/usr/bin/env python
"""
Seed script to populate initial categories for products app.
Run with: ./venv/bin/python seed_products_data.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/Users/mdsaifuddin/Desktop/SaifDev/QI-Management/Development/qi-manager')
django.setup()

from products.models import Category

def seed_categories():
    """Create initial categories for products and services"""
    
    categories_data = [
        {
            'name': 'CCTV',
            'description': 'Closed-circuit television systems and surveillance equipment',
            'is_active': True
        },
        {
            'name': 'Electrical',
            'description': 'Electrical systems, wiring, lighting, and power distribution',
            'is_active': True
        },
        {
            'name': 'Plumbing',
            'description': 'Plumbing systems, pipes, fixtures, and water distribution',
            'is_active': True
        },
        {
            'name': 'Aircon',
            'description': 'Air conditioning, HVAC, and climate control systems',
            'is_active': True
        },
        {
            'name': 'Maintenance',
            'description': 'General maintenance, repair, and upkeep services',
            'is_active': True
        },
        {
            'name': 'Security System',
            'description': 'Comprehensive security systems including access control and alarms',
            'is_active': True
        },
        {
            'name': 'Gate Automation',
            'description': 'Automated gate systems, barriers, and access control',
            'is_active': True
        }
    ]
    
    created_count = 0
    for category_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )
        if created:
            created_count += 1
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
    
    print(f"\nSeeding complete! Created {created_count} new categories.")

if __name__ == '__main__':
    seed_categories()