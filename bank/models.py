# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.safestring import mark_safe
from ckeditor_uploader.fields import RichTextUploadingField 
import datetime



# First, define the Manager subclass.
class ExaminationManager(models.Manager):
    def get_queryset(self):
        return super(ExaminationManager, self).get_queryset().filter(active=True)
   


class Examination(models.Model):
    name = models.CharField(max_length=20)
    subjects = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    duration = models.IntegerField(default=0)
    limit = models.IntegerField(default=0)

    objects = models.Manager()
    #active examination manager
    actv = ExaminationManager()

    def __str__(self):
        return self.name



class Subject(models.Model):
    examination = models.ForeignKey(
        Examination, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    to_do = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    compulsory = models.BooleanField(default=False)
    weight = models.DecimalField(
        default=1.00, max_digits=5, decimal_places=2)
    limit = models.IntegerField(default=0)

    # class Meta:
    #     order_with_respect_to = 'examination'


    # @property
    # def codename(self):
    #     exam = str(self.examination.name)[0:3]
    #     subj = str(self.name)[0:3]
    #     return exam+subj


    def __str__(self):
        return "%s (%s)" % (self.name, self.examination)



class Topic(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    to_do = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    # quantity of sub topic
    unit_subtopic = models.IntegerField(default=0)
    weight = models.DecimalField(
        default=1.00, max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class SubTopic(models.Model):
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    to_do = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    weight = models.DecimalField(
        default=1.00, max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name



class Question(models.Model):
    # examination = models.CharField(max_length=20)
    # subject = models.CharField(max_length=30)
    batch = models.CharField(max_length=30, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, blank=True, null=True)
    subtopic = models.ForeignKey(
        SubTopic, on_delete=models.SET_NULL, blank=True, null=True)
    # topic = models.CharField(max_length=100, default='General')
    # subtopic = models.CharField(
    #     max_length=100, default='General')
    question_text = RichTextUploadingField()
    a = RichTextUploadingField()
    b = RichTextUploadingField()
    c = RichTextUploadingField()
    d = RichTextUploadingField()
    e = RichTextUploadingField(blank=True, null=True)
    ans = models.CharField(max_length=1)


    @property
    def question(self):
        return mark_safe(self.question_text)

    @property
    def option_a(self):
        return mark_safe(self.a)

    @property
    def option_b(self):
        return mark_safe(self.b)

    @property
    def option_c(self):
        return mark_safe(self.c)

    @property
    def option_d(self):
        return mark_safe(self.d)

    @property
    def option_e(self):
        return mark_safe(self.e)

    def __str__(self):
        # return self.question_text.encode('utf-8')
        return mark_safe(self.question_text)
