# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-11-25 20:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mngr', '0008_auto_20181120_2246'),
    ]

    operations = [
        migrations.AddField(
            model_name='about',
            name='guidelines',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='about',
            name='partners_guidelines',
            field=models.TextField(blank=True, null=True),
        ),
    ]
