# QI Manager

A Django-based management system with Role-Based Access Control (RBAC) and comprehensive system settings management.

## Features

### User Management (RBAC)
- **Users**: Full CRUD operations with role assignments
- **Roles**: Create and manage roles with permission mappings
- **Permissions**: Fine-grained permission system with codename-based access control

### System Settings
- **Company Settings**: Logo, contact info, currency, timezone, date format
- **Email Configuration**: SMTP settings with TLS/SSL support
- **Email Templates**: Customizable templates for quotations, invoices, receipts, and notifications
- **Quotation Configuration**: Number format, terms, warranty, tax settings
- **Invoice Configuration**: Number format, footer, payment instructions, due days
- **Payment Methods**: Bank transfer, credit/debit cards, PayPal, Stripe, etc.
- **Payment Terms**: Net terms, custom due dates

### Authentication
- Standard Django authentication
- Google OAuth via allauth
- Role-based access control middleware

## Tech Stack

- **Backend**: Django 4.x
- **Frontend**: Bootstrap 5, jQuery, DataTables, SweetAlert2
- **Database**: SQLite (default), PostgreSQL compatible
- **Authentication**: Django allauth (Google OAuth)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd qi-manager
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django django-allauth python-dotenv whitenoise
```

4. Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Seed initial data:
```bash
python seed_data.py
python seed_settings_data.py
```

7. Create superuser:
```bash
python manage.py createsuperuser
```

8. Run development server:
```bash
python manage.py runserver
```

## URL Structure

| Path | Description |
|------|-------------|
| `/` | Index page (redirects to login/home) |
| `/login/` | Authentication login |
| `/logout/` | Authentication logout |
| `/home/` | Dashboard |
| `/profile/` | User profile |
| `/users/` | User list (Admin/Super Admin) |
| `/users/create/` | Create user |
| `/roles/` | Role list |
| `/permissions/` | Permission list |
| `/settings/` | System settings dashboard |

## RBAC Permissions

Access to admin sections is controlled by roles:
- **Super Admin**: Full access (delete users, manage permissions, settings)
- **Admin**: Manage users and roles (no delete privileges)

Middleware-based access control via `MIDDLEWARE_ROLE_MAP` in settings.

## API Endpoints

### DataTables (AJAX)
- `/ajax/users-datatable/` - Server-side user listing
- `/ajax/roles-datatable/` - Server-side role listing
- `/ajax/permissions-datatable/` - Server-side permission listing

### Dynamic Form Loading
- `/ajax/load-roles/?user_id=<id>` - Get user roles
- `/ajax/load-permissions/?role_id=<id>` - Get role permissions

## Project Structure

```
qi-manager/
├── accounts/           # RBAC app (User, Role, Permission models)
├── settings_app/       # System settings app
├── config/             # Django project configuration
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── seed_data.py        # Initial RBAC data seeding
├── seed_settings_data.py  # Initial settings seeding
└── manage.py
```

## Development

Run tests:
```bash
python manage.py test
```

Collect static files:
```bash
python manage.py collectstatic
```

## License

MIT License