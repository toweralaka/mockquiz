# Generated by Django 3.2.12 on 2022-02-05 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bank', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('site_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_period', models.DateField(null=True)),
                ('capacity', models.IntegerField(default=0)),
                ('filled', models.IntegerField(default=0)),
                ('number', models.CharField(max_length=2)),
                ('date', models.DateField(verbose_name='exam date')),
                ('time', models.TimeField(verbose_name='exam time')),
                ('active', models.BooleanField(default=True)),
                ('write_exam', models.BooleanField(default=False)),
                ('show_result', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ExamArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('exam_period', models.DateField(null=True)),
                ('candidates', models.IntegerField(default=0)),
                ('auto_batch', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExamCenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('exam_period', models.DateField(null=True)),
                ('candidates', models.IntegerField(default=0)),
                ('address', models.CharField(blank=True, max_length=1000, null=True)),
                ('active', models.BooleanField(default=True)),
                ('show_photocard', models.BooleanField(default=True)),
                ('check_when', models.DateField(blank=True, null=True)),
                ('cordon', models.BooleanField(default=False)),
                ('exam_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userprofile.examarea')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('surname', models.CharField(max_length=100)),
                ('sex', models.CharField(choices=[('F', 'Female'), ('M', 'Male')], max_length=1)),
                ('phone', models.CharField(max_length=13)),
                ('course', models.CharField(blank=True, max_length=100, null=True)),
                ('passport', models.ImageField(help_text='Maximum of 250kb.(50x50px)', upload_to='passport/%Y/%m')),
                ('regnum', models.CharField(max_length=10)),
                ('viewed_photocard', models.BooleanField(default=False)),
                ('seat', models.IntegerField(blank=True, null=True)),
                ('is_online', models.BooleanField(default=False)),
                ('regdate', models.DateTimeField(auto_now_add=True)),
                ('recieve_mails', models.BooleanField(default=True, verbose_name='Receive Emails?')),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='userprofile.batch')),
                ('exam_area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='userprofile.examarea')),
                ('exam_center', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='userprofile.examcenter')),
                ('exam_state', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='userprofile.state')),
                ('examination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bank.examination')),
                ('feedback', models.ForeignKey(blank=True, help_text='How did you hear about this mock?', null=True, on_delete=django.db.models.deletion.SET_NULL, to='site_manager.advert')),
                ('subject', models.ManyToManyField(to='bank.Subject')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(choices=[('online', 'online'), ('scratch_card', 'scratch card')], max_length=20)),
                ('reference', models.CharField(max_length=150)),
                ('amount', models.DecimalField(decimal_places=2, default=2000.0, max_digits=7)),
                ('amount_debited', models.DecimalField(decimal_places=2, max_digits=7)),
                ('amount_refunded', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userprofile.userprofile')),
            ],
        ),
        migrations.AddField(
            model_name='examarea',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userprofile.state'),
        ),
        migrations.AddField(
            model_name='batch',
            name='exam_center',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userprofile.examcenter'),
        ),
    ]
