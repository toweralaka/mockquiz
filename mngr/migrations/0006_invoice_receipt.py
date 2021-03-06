# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-13 22:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mngr', '0005_accesscode_freebie'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=13)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('particulars', models.TextField()),
                ('quantity', models.IntegerField()),
                ('amount', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cash', models.IntegerField()),
                ('cheque', models.IntegerField()),
                ('bank_name', models.CharField(max_length=50)),
                ('cheque_no', models.CharField(max_length=20)),
                ('words', models.TextField()),
                ('date', models.DateField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mngr.Invoice')),
            ],
        ),
    ]
