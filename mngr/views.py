# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
# from django.contrib.auth.decorators import login_required
# from django.views import generic
# from django.views.generic import View
from django.utils import timezone
from datetime import date, datetime, timedelta
# import pytz
import requests
import string
import random
import os
from django.conf import settings

# if settings.DEBUG:
# from Project.settings import MEDIA_ROOT
from PIL import Image


# Create your views here.
from .models import AccessCode, UsedCard, SiteView, About, InBox, Partner, Guideline, Gallery, BlogPost
from bank.models import Examination, Subject, Topic
from userprofile.models import (UserProfile, Result, ExamArea,
 State, ExamCenter, Batch)

from .forms import InBoxForm



def csrf_failure(request, reason=""):
    context_instance = {'message': 'message'}
    return render(request, 'mngr/csrf.html')


def get_ip_time(request):
    ip = request.META.get("HTTP_X_REAL_IP", None)
    if ip:
        user_ip = ip
    else:
        user_ip = request.META.get("REMOTE_ADDR", "")
    if request.method == 'POST':
        timespent = int(float(request.POST.get('user_time_spent')))
        try:
            dview = SiteView.objects.get(ip=user_ip, session=request.session.session_key)
            dview.time_spent += timespent
            dview.save()
        except Exception: pass


def get_ip(request, page):
    ip = request.META.get("HTTP_X_REAL_IP", None)
    if ip:
        user_ip = ip
    else:
        user_ip = request.META.get("REMOTE_ADDR", "")
    try:
        old_view = SiteView.objects.get(ip=user_ip, session=request.session.session_key)
        old_view.visit += 1
        old_view.save()
    except (KeyError, SiteView.DoesNotExist):
        import socket
        dns = str(socket.getfqdn(user_ip)).split('.')[-1]
        try:
            if int(dns):
                view = SiteView(ip=user_ip,
                                session=request.session.session_key,
                                page=page,
                                visit= '1')
                view.save()
            else: pass
        except ValueError: 
            if user_ip == '127.0.0.1':
                view = SiteView(ip='localhost',
                                session=request.session.session_key,
                                page=page,
                                visit= '1')
                view.save()
            else: pass


def send_bbn_sms(msg, smsto):
    sender = 'MockExamsng'
    to = smsto
    message = msg
    username = 'ollybab4love@yahoo.com'
    password = 'clonessms'

    payload={
        'username': username,
        'password': password,
        #'appid': appid,
        'sender': sender,
        'message': msg,
        'mobile': smsto,
        #'callback': 1
    }
    url='https://gateway.sms.bbnplace.com/api/sendtext.php'
    return requests.post(url, params=payload, verify=False)




def index(request):
    today = timezone.now().today()
    CURRENTYEAR = today.year
    #delete a week old unpaid users
    lastweek = (today - timedelta(8)).isoformat()
    weekold = UserProfile.objects.filter(regdate__lte=lastweek)
    
    try:
        blog = BlogPost.objects.filter(published__lte=today).order_by('?')[0]
    except Exception:
        blog = None
    allresults = Result.objects.filter(marked=True).order_by('?')
    results = []
    for k in allresults:
        if len(results) < 50:
            dpath = str(k.user.passport)
            ddpath = os.path.join(settings.MEDIA_ROOT, dpath)
            try:   
                dfile=Image.open(ddpath)
                results.append(k)
            except IOError: pass
        else:
            break
            
    for i in weekold:
        if not i.paid:
            duser = User.objects.get(username=i.user.username)
            i.delete()
            duser.delete()
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'home')
    context_instance = {'about':about, 'blog':blog, 'CURRENTYEAR':CURRENTYEAR, 'results':results}
    return render(request, 'mngr/index.html', context_instance)


def blogs(request):
    get_ip(request, 'blogs')
    today = timezone.now().today()
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    try:
        currentblog = BlogPost.objects.filter(published__lte=today).order_by('-published')[0]
    except Exception:
        currentblog = None
    try:
        favoriteblogs = BlogPost.objects.filter(published__lte=today).order_by('-likes', '-shares', '-published')[:5]
    except Exception:
        favoriteblogs = None
    all_blogs = BlogPost.objects.filter(published__lte=today).order_by('-published')
    paginator = Paginator(all_blogs, 5) # Show 5 per page
    page = request.GET.get('page')
    try:
        allblogs = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer, deliver first page.
        allblogs = paginator.page(1)
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        allblogs = paginator.page(paginator.num_pages)
    context_instance = {'about':about, 'currentblog':currentblog, 'allblogs':allblogs, 'favoriteblogs':favoriteblogs}
    return render(request, 'mngr/blogs.html', context_instance)


# def searchblog(request):
#     Entry.objects.filter(headline__search="+Django -jazz Python")
    
def blog(request, pk):
    get_ip(request, 'blog')
    today = timezone.now().today()
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    blog = BlogPost.objects.get(pk=pk)
    blog.views += 1
    blog.save()
    try:
        favoriteblogs = BlogPost.objects.filter(published__lte=today).order_by('-likes', '-shares', '-published')[:5]
    except Exception:
        favoriteblogs = None
    all_blogs = BlogPost.objects.filter(published__lte=today).order_by('-published')
    paginator = Paginator(all_blogs, 5) # Show 5 per page
    page = request.GET.get('page')
    try:
        allblogs = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer, deliver first page.
        allblogs = paginator.page(1)
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        allblogs = paginator.page(paginator.num_pages)
    context_instance = {'about':about, 'blog':blog, 'allblogs':allblogs, 'favoriteblogs':favoriteblogs}
    return render(request, 'mngr/blog.html', context_instance)

    # facebook htmlsharecode
    #         <div class="fb-share-button" data-href="http://mockexamsng.com/" 
    #         data-layout="button" data-size="small" data-mobile-iframe="true">
    #         <a target="_blank" href="{% url 'mngr:share' %}" 
    #         class="fb-xfbml-parse-ignore"><div id="custmbtn" 
    #         class="text-muted"><strong>Share</strong></div></a></div>

    # <div class="fb-share-button" data-href="http://mockexamsng.com/blog/1" 
    # data-layout="button_count" data-size="large" data-mobile-iframe="true">
    # <a target="_blank" 
    # href="https://www.facebook.com/sharer/sharer.php?u=http%3A%2F%2Fmockexamsng.com%2Fblog%2F1&amp;src=sdkpreparse" 
    # class="fb-xfbml-parse-ignore">Share</a></div>

#facebook shares
def share(request, pk):
    blog = BlogPost.objects.get(pk=pk)
    blog.shares += 1
    blog.save()
    return HttpResponseRedirect('https://www.facebook.com/sharer/sharer.php?u=http%3A%2F%2Fmockexamsng.com%2F&amp;src=sdkpreparse')

# def like(request, pk):
#     blog = BlogPost.objects.get(pk=pk)
#     blog.likes += 1
#     blog.save()
#     return HttpResponseRedirect('https://www.facebook.com/sharer/sharer.php?u=http%3A%2F%2Fmockexamsng.com%2F&amp;src=sdkpreparse')


#generate random numbers
def rannum(size, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#generate random letters
def ranlet(size, chars=string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))


def send_email(msgsub, msgbody, msgto):
    return requests.post(
        "https://api.mailgun.net/v3/mail.mockexamsng.org/messages",
        auth=("api", "apikey"),
        data={"from": "Mockexamsng <mail.mockexamsng.org>",
              "to": [msgto,],
              "subject": msgsub,
              "text": msgbody})


def send_sms(msg, smsto):
    sender = 'MockExamsng'      
    to = smsto         
    message = msg    
    typed = '0'       
    routing = '2'    
    token = 'zkyTl1ZnaJy4IYLqBv3HdLRhgyyAGETLmDyVyscKeXpx86twCviRqPBYc8FnbPRybFouzKT1OJcNT3cdpIiOFfcyB7TrLHdLIfPj'     
    schedule = ''   

    payload={
        'sender': sender,
        'to': to,
        'message': message,
        'type': typed,
        'routing': routing,
        'token': token,
        'schedule': schedule,
    }

    url = 'https://smartsmssolutions.com/api'
    return requests.post(url, params=payload, verify=False)



def logout_user(request):
    logout(request)

    return render(request, 'mngr/login.html')


def login_user(request):
    get_ip(request, 'login')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                userprofile = UserProfile.objects.get(user=request.user)
                if userprofile.paid:
                    return render(request, 'userprofile/profile.html', {'userprofile':userprofile})
                else:
                    logout(request)
                    return render(request, 'mngr/login.html', 
                        {'error_message': 'Your Payment Has Not Been Confirmed. Please Check Back Or Make Payment If You Have Not'})
            else:
                return render(request, 'mngr/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'mngr/login.html', {'error_message': 'Invalid Username or Password'})
    return render(request, 'mngr/login.html')
    


def partner(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = 'None'
    get_ip(request, 'salespoint')
    CURRENTYEAR = date.today().year
    partners = Partner.objects.all().order_by('state')
    context_instance={'partners':partners, 'about':about, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'mngr/partner.html', context_instance)


def contact(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = 'None'
    get_ip(request, 'contact')
    CURRENTYEAR = date.today().year
    c = About.objects.all()
    if c.exists()==False:
        contact = None
    else:
        contact = About.objects.all()[0]
    if request.method == 'POST':
        form = InBoxForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            msg=InBox(
                name=name,
                phone=phone,
                email=email,
                message=message)
            msg.save()
            form = InBoxForm()
            context_instance={'form':form,
            'error_message': 'Message Sent, we will get back to you soon',
            'CURRENTYEAR':CURRENTYEAR,
            'about':about,
             'contact':contact}
            return render(request, 'mngr/contact.html', context_instance)
        else:
            form = InBoxForm(request.POST)
        context_instance={'form':form,
        'error_message': 'Invalid Message',
        'CURRENTYEAR':CURRENTYEAR,
        'about':about,
         'contact':contact}
        return render(request, 'mngr/contact.html', context_instance)
    else:
        form = InBoxForm()
    context_instance={'form':form, 'contact':contact, 'about':about, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'mngr/contact.html', context_instance)


def guidelines(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = 'None'
    get_ip(request, 'guidelines')
    CURRENTYEAR = date.today().year
    guidelines = Guideline.objects.all()
    context_instance={'guidelines':guidelines, 'about':about, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'mngr/guidelines.html', context_instance)

def gallery(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = 'None'
    gal = Gallery.objects.all().order_by('?')
    get_ip(request, 'gallery')
    CURRENTYEAR = date.today().year
    context_instance={'gal':gal, 'about':about, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'mngr/gallery.html', context_instance)