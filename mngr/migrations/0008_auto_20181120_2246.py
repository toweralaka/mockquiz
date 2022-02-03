# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-11-20 22:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mngr', '0007_auto_20180214_0843'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('picture', models.ImageField(help_text='Maximum of 1mb.(1200x900px)', upload_to='galle/%Y/%m/%d')),
                ('description', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name_plural': 'gallery',
            },
        ),
        migrations.RenameField(
            model_name='fileuploads',
            old_name='doc',
            new_name='image',
        ),
        migrations.AlterField(
            model_name='accesscode',
            name='buyer',
            field=models.CharField(blank=True, default='-', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='accesscode',
            name='custom_center',
            field=models.CharField(blank=True, default='-', max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='inbox',
            name='subject',
            field=models.CharField(default='-', max_length=100),
        ),
        migrations.AlterField(
            model_name='siteview',
            name='page',
            field=models.CharField(default='-', max_length=20),
        ),
        migrations.AlterField(
            model_name='usedcard',
            name='buyer',
            field=models.CharField(default='-', max_length=30),
        ),
    ]