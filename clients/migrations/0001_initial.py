# Generated migration for clients app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255)),
                ('company_registration_no', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=30, null=True)),
                ('website', models.CharField(blank=True, max_length=255, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_clients', to='accounts.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_clients', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientContactPerson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_name', models.CharField(max_length=255)),
                ('designation', models.CharField(blank=True, max_length=150, null=True)),
                ('department', models.CharField(blank=True, max_length=150, null=True)),
                ('mobile_number', models.CharField(blank=True, max_length=30, null=True)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contact_persons', to='clients.client')),
            ],
            options={
                'verbose_name': 'Client Contact Person',
                'verbose_name_plural': 'Client Contact Persons',
                'ordering': ['-is_primary', 'person_name'],
            },
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['company_name'], name='idx_client_company'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['email'], name='idx_client_email'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['phone'], name='idx_client_phone'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['status'], name='idx_client_status'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['is_deleted'], name='idx_client_deleted'),
        ),
        migrations.AddIndex(
            model_name='clientcontactperson',
            index=models.Index(fields=['client_id'], name='idx_contact_client'),
        ),
        migrations.AddIndex(
            model_name='clientcontactperson',
            index=models.Index(fields=['email'], name='idx_contact_email'),
        ),
        migrations.AddIndex(
            model_name='clientcontactperson',
            index=models.Index(fields=['mobile_number'], name='idx_contact_mobile'),
        ),
        migrations.AddIndex(
            model_name='clientcontactperson',
            index=models.Index(fields=['is_primary'], name='idx_contact_primary'),
        ),
    ]