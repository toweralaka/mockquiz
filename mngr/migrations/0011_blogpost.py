# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-01-06 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mngr', '0010_auto_20181226_2213'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, unique=True)),
                ('content', models.TextField()),
                ('caption_image', models.ImageField(blank=True, null=True, upload_to=b'')),
                ('snippet', models.CharField(blank=True, max_length=100, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('published', models.DateTimeField(blank=True, null=True)),
                ('edited', models.DateTimeField(blank=True, null=True)),
                ('views', models.IntegerField(help_text="default is '0'")),
                ('likes', models.IntegerField(help_text="default is '0'")),
                ('shares', models.IntegerField(help_text="default is '0'")),
            ],
        ),
    ]