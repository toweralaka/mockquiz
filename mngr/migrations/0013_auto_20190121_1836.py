# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-01-21 18:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mngr', '0012_auto_20190114_2309'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postcomment',
            name='post',
        ),
        migrations.RemoveField(
            model_name='postcomment',
            name='user',
        ),
        migrations.AddField(
            model_name='about',
            name='instagram',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='about',
            name='pinterest',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='about',
            name='facebook',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='about',
            name='twitter',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.DeleteModel(
            name='PostComment',
        ),
    ]
