# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ckeditor_uploader.fields import RichTextUploadingField 
from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
import string
import random

# Create your models here.


class AccessCode(models.Model):
    name = models.CharField(max_length=50)
    pin = models.CharField(max_length=10)
    srn = models.CharField(max_length=10, blank=False, null=False)
    used = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    freebie = models.BooleanField(default=True) ##should card have freebie
    custom = models.BooleanField(default=False) ##special(customised)
    custom_center = models.CharField(max_length=1000, default='-', blank=True, null=True) ##special(customised) center requirement by buyer 
    #custom_center = models.ForeignKey(ExamCenter, on_delete=models.SET_NULL, default='-', blank=True, null=True)
    generated = models.DateTimeField(auto_now_add=True)
    buyer = models.CharField(max_length=30, default='-', blank=True, null=True)
    passcode = models.CharField(max_length=30, default='', blank=True, null=True)

    class Meta:
        unique_together = ('pin', 'srn')

    def __str__(self):
        return self.srn


class Freebie(models.Model):
    name = models.CharField(max_length=10)
    pin = models.CharField(max_length=10)
    srn = models.CharField(max_length=10, blank=False, null=False)
    uses = models.IntegerField(default=0)
    used = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    custom = models.BooleanField(default=False) 
    generated = models.DateTimeField(auto_now_add=True)
    unlimited = models.BooleanField(default=False)
    unlimited_until = models.DateTimeField(blank=True, null=True)
    user = models.CharField(max_length=10, default='-')
    expire = models.BooleanField(default=True)
    expiration = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return self.srn


class Advert(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


class UsedCard(models.Model):
    name = models.CharField(max_length=10)
    buyer = models.CharField(max_length=30, default='-')
    pin = models.CharField(max_length=10, blank=False, null=False)
    serial = models.CharField(max_length=10, blank=False, null=False)
    timeused = models.DateTimeField(auto_now_add=True)
    examination = models.CharField(max_length=20, blank=False, null=False)
    exam_area = models.CharField(max_length=50, blank=False, null=False)
    user = models.CharField(max_length=50, blank=False, null=False)


    def __str__(self):
        return self.serial



class Partner(models.Model):
    name = models.CharField(max_length=50)
    state = models.CharField(max_length=13, blank=True, null = True)
    local_govt = models.CharField(max_length=13, blank=True, null = True)
    phone = models.CharField(max_length=13, blank=True, null = True)
    address = models.CharField(max_length=100, blank=True, null = True)
    contact = models.CharField(max_length=50, blank=True, null = True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class SiteView(models.Model):
    page = models.CharField(max_length=20, default='-')
    ip = models.CharField(max_length=40)
    session = models.CharField(max_length=40, null=True)
    created = models.DateTimeField(auto_now_add=True)
    time_spent = models.IntegerField(default=0)
    visit = models.IntegerField(default=0)

    def __str__(self):
        return self.ip

    class Meta:
        verbose_name_plural = "Site Views"

class Guideline(models.Model):
    label = models.CharField(max_length=2)
    text = models.TextField()
    image = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.label


class About(models.Model):
    hotline1 = models.CharField(max_length=13)
    hotline2 = models.CharField(max_length=13, blank=True, null = True)
    email = models.EmailField()
    email2 = models.EmailField(blank=True, null=True)
    website = models.URLField()
    twitter = models.CharField(max_length=100, blank=True, null = True)
    facebook = models.CharField(max_length=100, blank=True, null = True)
    instagram = models.CharField(max_length=100, blank=True, null = True)
    pinterest = models.CharField(max_length=100, blank=True, null = True)
    office = models.CharField(max_length=50, blank=True, null = True)
    guidelines = models.TextField(blank=True, null=True)
    partners_guidelines = models.TextField(blank=True, null=True)
    prepare = models.TextField(blank=True, null=True)
    practise = models.TextField(blank=True, null=True)
    measure = models.TextField(blank=True, null=True)
    page = models.CharField(max_length=50, blank=True, null=True)
    meta_title = models.CharField(max_length=65, blank=True, null=True)
    meta_description = models.CharField(max_length=150, blank=True, null=True)
    meta_image = models.ImageField(upload_to="about/", blank=True, null=True)


    def __str__(self):
        return self.page

    class Meta:
        verbose_name_plural = "About"


class FileUploads(models.Model):
    name = models.CharField(max_length=10)
    image = models.FileField(upload_to='files/%Y/%m')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "File Uploads"


class InBox(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=13)
    email = models.EmailField()
    subject = models.CharField(max_length=100, default='-')
    message = models.CharField(max_length=1000)
    time_in = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Inboxes"
        #unique_together = ('email', 'subject')



class Invoice(models.Model):
    client = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=13)
    email = models.EmailField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    particulars = models.TextField()
    quantity = models.IntegerField()
    amount = models.IntegerField()
    transaction_date = models.DateField(blank= False,null=True)

    @property
    def ref(self):
        no = self.id
        first_letters = self.client[:2]
        last_letters = self.client[-2:]
        yr = self.date.year
        month = self.date.month
        day = self.date.day
        return str(yr) + '/' + str(first_letters).upper() + '0' + str(no) + '0' + str(day) + '0' + str(month) + str(last_letters).upper()

    @property
    def balance(self):
        all_receipt = self.receipt_set.all()
        pd = 0
        for i in all_receipt:
            pd = pd + i.total
        bal = self.amount - pd
        return bal


    def __str__(self):
        return self.ref


class Receipt(models.Model):
    client = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    cash = models.IntegerField()
    cheque = models.IntegerField()
    bank_name = models.CharField(max_length=50)
    cheque_no = models.CharField(max_length=20)
    #totald = models.IntegerField() #remove
    words = models.TextField()
    date = models.DateField(auto_now_add=True)
    transaction_date = models.DateField(blank= False,null=True)

    @property
    def total(self):
        tot = self.cash + self.cheque
        return tot

    def __str__(self):
        return self.client.client


class Gallery(models.Model):
    name = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='galle/%Y/%m/%d', help_text=("Maximum of 1mb.(1200x900px)"))
    description = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "gallery"

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200, unique=True)
    content = RichTextUploadingField()
    caption_image = models.ImageField(null=True, blank=True)
    snippet = models.CharField(null=True, blank=True, max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    published = models.DateTimeField(null=True, blank=True)
    edited = models.DateTimeField(null=True, blank=True)
    views = models.IntegerField(help_text="default is '0'")
    likes = models.IntegerField(help_text="default is '0'")
    shares = models.IntegerField(help_text="default is '0'")

    def __str__(self):
        return self.title





class BlogUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)


# class PostComment(models.Model):
#     user = models.ForeignKey(BlogUser)
#     post = models.ForeignKey(BlogPost)
#     comment = models.TextField()
#     like = models.BooleanField()
#     share = models.BooleanField()
#     time_in = models.DateTimeField(auto_now_add=True)
#     approved = models.BooleanField()
    #favorite =

# class Engagement(models.Model):
#     page = models.CharField(max_length=50)
#     date = models.DateField(auto_now_add=True)
#     clickcounts = models.IntegerField()