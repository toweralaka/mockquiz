# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-14 15:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examcenter',
            name='address',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='examcenter',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
