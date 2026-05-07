#!/usr/bin/env python
"""Setup Google OAuth provider"""
import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Configure site
site, _ = Site.objects.get_or_create(
    id=1,
    defaults={'domain': 'localhost:8000', 'name': 'QI Manager'}
)

# Create Google Social App
google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

if google_client_id and google_client_secret:
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': google_client_id,
            'secret': google_client_secret,
        }
    )
    if created:
        app.sites.add(site)
        print('✓ Google OAuth configured successfully')
    else:
        print('✓ Google OAuth already configured')
else:
    print('! Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env')

print(f'✓ Site configured: {site.domain}')