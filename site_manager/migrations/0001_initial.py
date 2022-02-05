# Generated by Django 3.2.12 on 2022-02-05 17:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('flatpages', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='About',
            fields=[
                ('flatpage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='flatpages.flatpage')),
                ('product_name', models.CharField(max_length=250)),
                ('hotlines', models.CharField(max_length=250)),
                ('email', models.EmailField(max_length=254)),
                ('email2', models.EmailField(blank=True, max_length=254, null=True)),
                ('website', models.URLField()),
                ('twitter', models.URLField(blank=True, null=True)),
                ('facebook', models.URLField(blank=True, null=True)),
                ('instagram', models.URLField(blank=True, null=True)),
                ('pinterest', models.URLField(blank=True, null=True)),
                ('office', models.CharField(blank=True, max_length=250, null=True)),
                ('prepare_text', models.TextField(blank=True, null=True)),
                ('practise_text', models.TextField(blank=True, null=True)),
                ('measure_text', models.TextField(blank=True, null=True)),
                ('meta_title', models.CharField(blank=True, max_length=150, null=True)),
                ('meta_description', models.CharField(blank=True, max_length=250, null=True)),
                ('meta_image', models.ImageField(blank=True, null=True, upload_to='about/')),
            ],
            options={
                'verbose_name_plural': 'About',
            },
            bases=('flatpages.flatpage',),
        ),
        migrations.CreateModel(
            name='AccessCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('pin', models.CharField(max_length=10)),
                ('serial_number', models.CharField(max_length=10)),
                ('used', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('freebie', models.BooleanField(default=False, help_text='should card have freebie')),
                ('custom', models.BooleanField(default=False)),
                ('custom_center', models.CharField(blank=True, max_length=1000, null=True)),
                ('generated', models.DateTimeField(auto_now_add=True)),
                ('buyer', models.CharField(blank=True, max_length=30, null=True)),
                ('passcode', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'unique_together': {('pin', 'serial_number')},
            },
        ),
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Guideline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=2)),
                ('text', models.TextField()),
                ('image', models.FileField(blank=True, null=True, upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='SiteView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page', models.CharField(default='-', max_length=20)),
                ('ip', models.CharField(max_length=40)),
                ('session', models.CharField(max_length=40, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('time_spent', models.IntegerField(default=0)),
                ('visit', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Site Views',
            },
        ),
        migrations.CreateModel(
            name='CardUse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeused', models.DateTimeField(auto_now_add=True)),
                ('access_code', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='site_manager.accesscode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
