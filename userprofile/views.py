# -*- coding: utf-8 -*-
from __future__ import unicode_literals 

from django.shortcuts import render, render_to_response
from django.http import HttpResponseRedirect
from django.contrib import messages # add context to HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.utils import timezone

from datetime import date
import string
import random

from .models import (UserProfile, ExamArea, ExamCenter, Batch, Result, SubjectScore, 
SpecialCase, State, Referrer, Referral, BankDirect, SupReferral)
from bank.models import Subject, Examination
from mngr.models import AccessCode, UsedCard, SiteView, About, Freebie
from .forms import (UserProfileForm, UserForm, SubjectForm, UpdateProfileForm, ReferrerForm,
        RefUserProfileForm, ReferralLoginForm, BankDirectForm, ReBankDirectForm)
from mngr.views import get_ip, send_sms, rannum, ranlet

IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']
# Create your views here.




def subject_request(request):
    if request.method== 'POST':
        choice_exam = request.POST.get('examination')
        exam = Examination.objects.get(id=str(choice_exam))
        compulsory = exam.subject_set.filter(compulsory=True)
        selected = len(compulsory)
        totals = exam.subjects
        unit = totals - selected
        subject = exam.subject_set.order_by('-compulsory', 'name')
    return render_to_response('userprofile/subject_request.html', {'subject':subject, 'unit': unit})


def area_request(request):
    if request.method== 'POST':
        choice_state = request.POST.get('exam_state')
        state = State.objects.get(id=str(choice_state))
        area = state.examarea_set.filter(active=True).order_by('name')
    return render_to_response('userprofile/area_request.html', {'area':area,})



def reg_profile(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'registration')
    today = timezone.now().today()
    CURRENTYEAR = today.year
    if request.method == 'POST':
        uform = UserForm(request.POST)
        pform = UserProfileForm(request.POST, request.FILES)
        sform = SubjectForm(request.POST)
        if uform.is_valid() and pform.is_valid() and sform.is_valid():
            user = uform.save(commit=False)
            password = uform.cleaned_data['password1']
            email = uform.cleaned_data['email']
            user.set_password(password)
            user.save()
            dg = rannum(8)
            lt = ranlet(2)
            regcode = str(dg) + lt
            user.username = regcode
            user.save()
            userprofile, new = UserProfile.objects.get_or_create(user=user)
            subject = sform.cleaned_data['subject']
            first_name = pform.cleaned_data['first_name']
            surname = pform.cleaned_data['surname']
            exam_area = pform.cleaned_data['exam_area']
            examination = pform.cleaned_data['examination']
            feedback = pform.cleaned_data['feedback']
            pin = pform.cleaned_data['pin']
            serial = pform.cleaned_data['serial']
            course = pform.cleaned_data['course']
            exam_state = pform.cleaned_data['exam_state']
            phone = pform.cleaned_data['phone']
            sex = pform.cleaned_data['sex']
            passport = pform.cleaned_data['passport']

            code = AccessCode.objects.get(pin=pin, srn=serial)
            userprofile.exam_area = exam_area
            userprofile.first_name = first_name
            userprofile.surname = surname
            userprofile.sex = sex
            userprofile.examination = examination
            userprofile.feedback = feedback
            userprofile.pin = pin
            userprofile.paid = True
            userprofile.serial = serial
            userprofile.course = course
            userprofile.exam_state = exam_state
            for sub in subject:
                userprofile.subject.add(sub)
            userprofile.phone = phone
            userprofile.regnum = regcode
            userprofile.passport = passport
            userprofile.save()

            code.used = True
            code.save()

            card = UsedCard(
            pin = pin,
            serial = serial,
            examination = examination,
            exam_area = exam_area,
            user = user.username)
            card.save()

            mesgbody = 'Mockexamsng Registration Successful! Registration Number: '+ str(userprofile.regnum) + '.'
            smesto = str(userprofile.phone)
            # try:
            #     send_sms(mesgbody, smesto)
            # except Exception:
            #     pass
            user = authenticate(username=regcode, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.add_message(request, messages.INFO, 
                        'Registration Successful! Registration Number: '+ str(userprofile.regnum) + '.')
                    return HttpResponseRedirect('/user/profile/')
                else:
                    return render(request, 'mngr/login.html', {'error_message': 'Your account has been disabled'})
            else:
                return render(request, 'mngr/login.html', {'error_message': 'Invalid Username or Password'})
            context_instance={'userprofile':userprofile,
            'error_message': 'Registration Successful! Registration Number: '+ str(userprofile.regnum) + '.'}
            return render(request, 'userprofile/profile.html', context_instance)
        else:
            context_instance = {'uform': uform,
             'pform': pform,
              'sform': sform,
              'CURRENTYEAR':CURRENTYEAR,
              'about':about,
              'error_message': 'Invalid Registration!'}

            return render(request, 'userprofile/reg_profile.html', context_instance)
    else:
        get_ip(request, 'register')
        uform = UserForm()
        pform = UserProfileForm()
        sform = SubjectForm()
        context_instance = {'uform': uform, 'about':about,
        'pform': pform, 'sform': sform, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'userprofile/reg_profile.html', context_instance)


@login_required
def profile(request):
    if request.user.is_authenticated() and not request.user.is_staff:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
            if userprofile.paid:
                dbatch = None
                #batch to custom center
                card = AccessCode.objects.get(srn=userprofile.serial, pin=userprofile.pin)
                if card.custom:
                    try:
                        ucenter = ExamCenter.actv.filter(name=card.custom_center, active=True)[0]
                    except ExamCenter.DoesNotExist:
                        pass
                    else:
                        userprofile.exam_center = ucenter
                        userprofile.save()
                        dcenter = ExamCenter.objects.get(name=ucenter.name, exam_period=ucenter.exam_period)
                        b = Batch.actv.filter(exam_center=dcenter).order_by('-filled')
                        if b.exists()==False:
                            pass
                        else:
                            btch = b[0]
                            if not userprofile.batch: 
                                if btch.capacity > btch.qty:
                                    btch.filled = btch.qty
                                    btch.filled += 1
                                    btch.save()
                                    userprofile.batch = btch
                                    if not UserProfile.objects.filter(batch=btch,seat=btch.filled).exists():
                                        userprofile.seat = btch.filled
                                    userprofile.pc = True
                                    userprofile.save()
                                else:
                                    pass
                            elif not userprofile.seat:
                                count = 1
                                usbatch = userprofile.batch
                                while count <= usbatch.qty:
                                    if UserProfile.objects.filter(batch=usbatch, seat=count).exists():
                                        count +=1
                                    else:
                                        userprofile.seat = count
                                        userprofile.pc = True
                                        userprofile.save()
                                        count = usbatch.qty
                else:
                    exam_state = userprofile.exam_state
                    userarea = userprofile.exam_area
                    area = ExamArea.objects.get(name=userarea.name, exam_period=userarea.exam_period)
                    if area.auto_batch == False:
                        pass
                    else:
                        area.candidates = area.qty
                        area.save()

                        centers = ExamCenter.actv.filter(exam_area=area, cordon=False).order_by('candidates')
                        if centers.exists()== False:
                            pass
                        elif not userprofile.exam_center:
                            ucenter = centers[0]
                            userprofile.exam_center = ucenter
                            userprofile.save()             
                        else:
                            ucenter = userprofile.exam_center

                            dcenter = ExamCenter.objects.get(name=ucenter.name, exam_period=ucenter.exam_period)
                            b = Batch.actv.filter(exam_center=dcenter).order_by('filled')
                            if b.exists()==False:
                                pass
                            else:
                                btch = b[0]
                                if not userprofile.batch: 
                                    if btch.capacity > btch.qty:
                                        btch.filled = btch.qty
                                        btch.filled += 1
                                        btch.save()
                                        userprofile.batch = btch
                                        if not UserProfile.objects.filter(batch=btch,seat=btch.filled).exists():
                                            userprofile.seat = btch.filled
                                        userprofile.pc = True
                                        userprofile.save()
                                    else:
                                        pass
                                elif not userprofile.seat:
                                    count = 1
                                    usbatch = userprofile.batch
                                    while count <= usbatch.qty:
                                        if UserProfile.objects.filter(batch=usbatch, seat=count).exists():
                                            count +=1
                                        else:
                                            userprofile.seat = count
                                            userprofile.pc = True
                                            userprofile.save()
                                            count = usbatch.qty


                if not userprofile.exam_center:
                    centerd = None
                else:
                    centerd = ExamCenter.objects.get(name=userprofile.exam_center.name, exam_period=userprofile.exam_center.exam_period)
                b = Batch.actv.filter(exam_center=centerd)
                try:
                    b[0]
                    batches = True
                except IndexError:
                    batches = False
                if not userprofile.batch:
                    dbatch = None
                else:
                    dbatch = Batch.objects.get(number=str(userprofile.batch.number), exam_center=userprofile.exam_center)
                context_instance = {'userprofile':userprofile, 
                'centerd':centerd,
                'dbatch': dbatch,
                'batches': batches}
                return render(request, 'userprofile/profile.html', context_instance)
            else:
                logout(request)
                messages.add_message(request, messages.INFO, 
                "Your Payment Has Not Been Confirmed. Please Check Back Or Make Payment If You Have Not")
                return HttpResponseRedirect('/login/')
        except UserProfile.DoesNotExist:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/login/')

        
    
    



def profileupdate(request):
    if request.user.is_authenticated() and not request.user.is_staff:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
            if userprofile.paid:
                pform = UpdateProfileForm(request.POST or None, request.FILES or None, instance=userprofile)
                sform = SubjectForm(request.POST or None, instance=userprofile)
                if request.method == 'POST':
                    if pform.is_valid() and sform.is_valid():
                        pform.save()
                        sform.save()
                        return HttpResponseRedirect('/user/profile/')
                context_instance={'pform': pform, 'sform': sform, 'userprofile':userprofile}
                return render(request, 'userprofile/userprofile_form.html', context_instance)
            else:
                logout(request)
                messages.add_message(request, messages.INFO, 
                "Your Payment Has Not Been Confirmed. Please Check Back Or Make Payment If You Have Not")
                return HttpResponseRedirect('/login/')
        except UserProfile.DoesNotExist:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/login/')
        

    

@login_required
def photocard(request):
    if request.user.is_authenticated() and not request.user.is_staff:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
            if userprofile.paid:
                dbatch = None
                #batch to custom center
                card = AccessCode.objects.get(srn=userprofile.serial, pin=userprofile.pin)

                if card.custom:
                    try:
                        ucenter = ExamCenter.actv.filter(name=card.custom_center, active=True)[0]
                    except ExamCenter.DoesNotExist:
                        pass
                    else:
                        userprofile.exam_center = ucenter
                        userprofile.save()
                        dcenter = ExamCenter.objects.get(name=ucenter.name, exam_period=ucenter.exam_period)
                        b = Batch.actv.filter(exam_center=dcenter).order_by('-filled')
                        if b.exists()==False:
                            pass
                        else:
                            btch = b[0]
                            if not userprofile.batch: 
                                if btch.capacity > btch.qty:
                                    btch.filled = btch.qty
                                    btch.filled += 1
                                    btch.save()
                                    userprofile.batch = btch
                                    if not UserProfile.objects.filter(batch=btch,seat=btch.filled).exists():
                                        userprofile.seat = btch.filled
                                    userprofile.pc = True
                                    userprofile.save()
                                else:
                                    pass
                            elif not userprofile.seat:
                                count = 1
                                usbatch = userprofile.batch
                                while count <= usbatch.qty:
                                    if UserProfile.objects.filter(batch=usbatch, seat=count).exists():
                                        count +=1
                                    else:
                                        userprofile.seat = count
                                        userprofile.pc = True
                                        userprofile.save()
                                        count = usbatch.qty
                else:
                    exam_state = userprofile.exam_state
                    userarea = userprofile.exam_area
                    area = ExamArea.objects.get(name=userarea.name, exam_period=userarea.exam_period)
                    if area.auto_batch == False:
                        pass
                    else:
                        area.candidates = area.qty
                        area.save()

                        centers = ExamCenter.actv.filter(exam_area=area, cordon=False).order_by('candidates')
                        if centers.exists()== False:
                            pass
                        elif not userprofile.exam_center:
                            ucenter = centers[0]
                            userprofile.exam_center = ucenter
                            userprofile.save()             
                        else:
                            ucenter = userprofile.exam_center

                            dcenter = ExamCenter.objects.get(name=ucenter.name, exam_period=ucenter.exam_period)
                            b = Batch.actv.filter(exam_center=dcenter).order_by('filled')
                            if b.exists()==False:
                                pass
                            else:
                                btch = b[0]
                                if not userprofile.batch: 
                                    if btch.capacity > btch.qty:
                                        btch.filled = btch.qty
                                        btch.filled += 1
                                        btch.save()
                                        userprofile.batch = btch
                                        if not UserProfile.objects.filter(batch=btch,seat=btch.filled).exists():
                                            userprofile.seat = btch.filled
                                        userprofile.pc = True
                                        userprofile.save()
                                    else:
                                        pass
                                elif not userprofile.seat:
                                    count = 1
                                    usbatch = userprofile.batch
                                    while count <= usbatch.qty:
                                        if UserProfile.objects.filter(batch=usbatch, seat=count).exists():
                                            count +=1
                                        else:
                                            userprofile.seat = count
                                            userprofile.pc = True
                                            userprofile.save()
                                            count = usbatch.qty

                if not userprofile.exam_center:
                    centerd = None
                else:
                    centerd = ExamCenter.objects.get(name=userprofile.exam_center.name, exam_period=userprofile.exam_center.exam_period)
                b = Batch.actv.filter(exam_center=centerd)
                try:
                    b[0]
                    batches = True
                except IndexError:
                    batches = False
                if not userprofile.batch:
                    dbatch = None
                else:
                    dbatch = Batch.objects.get(number=str(userprofile.batch.number), exam_center=userprofile.exam_center)
                
                card = None
                if userprofile.pc:
                    card = True
                context_instance={'userprofile':userprofile, 'card':card}
                return render(request, 'userprofile/photocard.html', context_instance)
            else:
                logout(request)
                messages.add_message(request, messages.INFO, 
                "Your Payment Has Not Been Confirmed. Please Check Back Or Make Payment If You Have Not")
                return HttpResponseRedirect('/login/')
        except UserProfile.DoesNotExist:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/login/')


@login_required
def result(request):
    if request.user.is_authenticated() and not request.user.is_staff:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
            if userprofile.paid:
                total = 0
                if userprofile.exam_center:
                    loc = ExamCenter.objects.get(name=userprofile.exam_center.name, exam_period=userprofile.exam_center.exam_period)
                else:
                    loc = False
                try:
                    result = Result.objects.get(user=userprofile)
                    scores = SubjectScore.objects.filter(user=str(userprofile.regnum))
                    for sc in scores:
                        total += int(sc.score)
                except Result.DoesNotExist:
                    result = False
                context_instance={'userprofile':userprofile, 'result':result, 'loc':loc, 'total':total}
                return render(request, 'userprofile/result.html', context_instance)
            else:
                logout(request)
                messages.add_message(request, messages.INFO, 
                "Your Payment Has Not Been Confirmed. Please Check Back Or Make Payment If You Have Not")
                return HttpResponseRedirect('/login/')
        except UserProfile.DoesNotExist:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/login/')


# def ref_profile_login(request):
#     today = timezone.now().today()
#    CURRENTYEAR = today.year
#     if request.method =='POST':
#         rform = ReferralLoginForm(request.POST)
#         if rform.is_valid():
#             phone_number = rform.cleaned_data['phone_number']
#             d_referrer = Referrer.objects.get(phone_number=phone_number)
#             referrer = Referral.objects.filter(referrer=d_referrer, active=True)
#             context_instance={'referrer':referrer,'CURRENTYEAR':CURRENTYEAR}
#             print(rform.errors)
#             print(d_referrer)
#             return render(request, 'userprofile/referrer_page.html', context_instance)
#         else:
#             return HttpResponseRedirect('/user/our_partner/')
#     else:
#         return HttpResponseRedirect('/user/our_partner/')
def referrer_page(request, pk):
    today = timezone.now().today()
    CURRENTYEAR = today.year
    get_ip(request, 'referrer')
    referrer = Referrer.objects.get(pk=pk)
    referred = Referral.objects.filter(referrer=referrer, active=True)
    sub_ref = []
    #get all sub_referrers
    sub_referrers = Referrer.objects.filter(referrer_code=referrer.ref_code)
    for i in sub_referrers:
        #the referrals of sub_referrers
        sub_referred = Referral.objects.filter(referrer=i, active=True)
        #is referral connected to a SupReferral
        sup_ref = None
        for j in sub_referred:
            try:
                sup_ref = SupReferral.objects.get(referral=j)
            except SupReferral.DoesNotExist:
                sup_ref = None
        payload = {'sub_referrer':i, 'sub_referred':sub_referred, 'sup_ref':sup_ref}
        sub_ref.append(payload)
    context_instance={'referrer':referrer,'referred':referred, 'sub_ref':sub_ref, 'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'userprofile/referrer_page.html', context_instance)


def ref_profile_login(request):
    if request.method =='POST':
        phone_number = request.POST['phone_number']
        try:
            referrer = Referrer.objects.get(phone_number=phone_number)
            pk = referrer.pk
            return HttpResponseRedirect('/user/referrer/'+str(pk))
            #return render(request, 'userprofile/referrer_page.html', context_instance)
        except Referrer.DoesNotExist:
            messages.add_message(request, messages.INFO, "You Need To Register To Partner With Us")
            return HttpResponseRedirect('/user/our_partner/')
    else:
        return HttpResponseRedirect('/user/our_partner/')

# def ref_profile(request):
#     today = timezone.now().today()
    CURRENTYEAR = today.year
#     d_referrer = Referrer.objects.get(phone_number=phone_number)
    
#     context_instance={'d_referrer':d_referrer,'CURRENTYEAR':CURRENTYEAR}
#     return render(request, 'userprofile/referrer_page.html', context_instance)    

# from django.contrib.messages import get_messages

# def my_view(request):
#     # Process your form data from the POST, or whatever you need to do

#     # Add the messages, as mentioned above
#     messages.add_message(request, messages.INFO, form.cleaned_data['name'])

#     return HttpResponseRedirect('/other_view_url/')

# def other_view(request):
#     storage = get_messages(request)
#     name = None
#     for message in storage:
#         name = message
#         break
#     return render(request, 'general/other_view.html', {'name': name})

def make_payment(request):
    return render (request, 'userprofile/payment.html')


def bank_payment(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'payment')
    today = timezone.now().today()
    CURRENTYEAR = today.year
    if request.method == 'POST':
        tform = ReBankDirectForm(request.POST)
        if tform.is_valid():
            email = tform.cleaned_data['email']
            payment_date = tform.cleaned_data['payment_date']
            amount = tform.cleaned_data['amount']
            bank = tform.cleaned_data['bank']
            depositor_name = tform.cleaned_data['depositor_name']
            transaction_id = tform.cleaned_data['transaction_id']
            payment_mode = tform.cleaned_data['payment_mode']
            try:
                userprofile = UserProfile.objects.get(user__username=email)
                paying = BankDirect(
                    user = userprofile,
                    payment_date = payment_date,
                    amount = amount,
                    bank = bank,
                    depositor_name = depositor_name,
                    transaction_id = transaction_id,
                    payment_mode = payment_mode)
                paying.save()
                messages.add_message(request, messages.INFO, "SUBMIT SUCCESSFUL! Login With Email.")
                return HttpResponseRedirect('/login/')
            except Exception:
                context_instance = {
                  'tform': tform,
                  'about':about,
                  'CURRENTYEAR':CURRENTYEAR,
                  'error_message': 'UNSUCCESSFUL! Please Enter Email Address Used During Registration.'}
                return render(request, 'userprofile/bank_pay.html', context_instance)
        else:
            context_instance = {
              'tform': tform,
              'about':about,
              'CURRENTYEAR':CURRENTYEAR,
              'error_message': 'Invalid Registration!'}
            return render(request, 'userprofile/bank_pay.html', context_instance)
    else:
        tform = ReBankDirectForm()
        context_instance = {
              'tform': tform,
              'about':about,
              'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'userprofile/bank_pay.html', context_instance)

    

def online_payment(request):
    return HttpResponseRedirect('https://paystack.com/pay/mockexamsngsubscription')


def referral(request):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'partnership')
    rform = ReferralLoginForm()
    today = timezone.now().today()
    CURRENTYEAR = today.year
    if request.method == 'POST':
        form = ReferrerForm(request.POST)
        if form.is_valid():
            dgs = rannum(4)
            lts = ranlet(1)
            full_name = form.cleaned_data['full_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            state = form.cleaned_data['state']
            referrer_code = form.cleaned_data['referrer_code']
            person = Referrer(
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                state=state,
                referrer_code=referrer_code,
                ref_code=lts+dgs)
            person.save()
            try:
                referrer = Referrer.objects.get(phone_number=phone_number)
                referrered = Referral.objects.filter(referrer=referrer, active=True)
                context_instance={'referrer':referrer,'referrered':referrered,'CURRENTYEAR':CURRENTYEAR}
                return render(request, 'userprofile/referrer_page.html', context_instance)
            except Referrer.DoesNotExist:
                messages.add_message(request, messages.INFO, "You Need To Register To Partner With Us")
                return HttpResponseRedirect('/user/our_partner/')
        else:
            context_instance = {'form': form,
            'rform': rform,
            'about':about,
              'CURRENTYEAR':CURRENTYEAR,
              'error_message': 'Invalid Registration!'}

            return render(request, 'userprofile/referrer.html', context_instance)
    else:
        form = ReferrerForm()
    return render(request, 'userprofile/referrer.html', 
        {'form': form, 'rform': rform, 'about':about, 'CURRENTYEAR':CURRENTYEAR})



def sub_referral(request, code):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'sub-referral')
    rform = ReferralLoginForm()
    today = timezone.now().today()
    CURRENTYEAR = today.year
    if request.method == 'POST':
        form = ReferrerForm(request.POST)
        if form.is_valid():
            dgs = rannum(4)
            lts = ranlet(1)
            full_name = form.cleaned_data['full_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            state = form.cleaned_data['state']
            referrer_code = form.cleaned_data['referrer_code']
            person = Referrer(
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                state=state,
                ref_code=lts+dgs)
            person.save()
            if referrer_code==code:
                person.referrer_code = code
                person.save()
            else:
                try:
                    referrer = Referrer.objects.get(ref_code=code)
                    person.referrer_code = code
                    person.save()
                except Referrer.DoesNotExist:
                    try:
                        referrer = Referrer.objects.get(ref_code=referrer_code)
                        person.referrer_code = referrer_code
                        person.save()
                    except Referrer.DoesNotExist:
                        person.referrer_code = 'Y907'
                        person.save()
            try:
                referrer = Referrer.objects.get(phone_number=phone_number)
                referrered = Referral.objects.filter(referrer=referrer, active=True)
                context_instance={'referrer':referrer,'referrered':referrered,'CURRENTYEAR':CURRENTYEAR}
                return render(request, 'userprofile/referrer_page.html', context_instance)
            except Referrer.DoesNotExist:
                messages.add_message(request, messages.INFO, "You Need To Register To Partner With Us")
                return HttpResponseRedirect('/user/referral/sub/'+str(code))
        else:
            context_instance = {'form': form,
            'rform': rform,
            'about':about,
              'CURRENTYEAR':CURRENTYEAR,
              'error_message': 'Invalid Registration!'}

            return render(request, 'userprofile/sub_referrer.html', context_instance)
    else:
        form = ReferrerForm()
    return render(request, 'userprofile/sub_referrer.html', 
        {'form': form, 'rform': rform, 'about':about, 'CURRENTYEAR':CURRENTYEAR})


def ref_reg_profile(request, code):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'referral')
    today = timezone.now().today()
    CURRENTYEAR = today.year
    referrer = Referrer.objects.get(ref_code=code)
    if request.method == 'POST':
        uform = UserForm(request.POST)
        pform = RefUserProfileForm(request.POST, request.FILES)
        sform = SubjectForm(request.POST)
        if uform.is_valid() and pform.is_valid() and sform.is_valid():
            user = uform.save(commit=False)
            # dg = rannum(8)
            # lt = ranlet(2)
            # username = uform.cleaned_data['username']
            password = uform.cleaned_data['password1']
            email = uform.cleaned_data['email']
            user.set_password(password)
            user.save()
            dg = rannum(8)
            lt = ranlet(2)
            regcode = str(dg) + lt
            user.username = regcode
            user.save()
            subject = sform.cleaned_data['subject']
            userprofile, new = UserProfile.objects.get_or_create(user=user)
            first_name = pform.cleaned_data['first_name']
            surname = pform.cleaned_data['surname']
            exam_area = pform.cleaned_data['exam_area']
            examination = pform.cleaned_data['examination']
            feedback = pform.cleaned_data['feedback']
            course = pform.cleaned_data['course']
            exam_state = pform.cleaned_data['exam_state']
            phone = pform.cleaned_data['phone']
            sex = pform.cleaned_data['sex']
            referral_code = pform.cleaned_data['referral_code']
            passport = pform.cleaned_data['passport']

            userprofile.exam_area = exam_area
            userprofile.first_name = first_name
            userprofile.surname = surname
            userprofile.sex = sex
            userprofile.referral_code = referral_code
            userprofile.examination = examination
            userprofile.feedback = feedback
            userprofile.payment_mode = 'online'
            userprofile.pin = '0000000000'
            userprofile.serial = 'ONLINE'
            userprofile.course = course
            userprofile.exam_state = exam_state
            userprofile.paid = False
            for sub in subject:
                userprofile.subject.add(sub)
            userprofile.phone = phone
            userprofile.regnum = regcode
            userprofile.passport = passport
            userprofile.save()

            #credit referrer
            try:
                referrer = Referrer.objects.get(ref_code=code)
                refd = Referral(
                    user_activated = userprofile,
                    active=False,
                    referrer = referrer)
                refd.save()
            except Referrer.DoesNotExist:
                referrer = Referrer.objects.get(ref_code='Y907')
                refd = Referral(
                    user_activated = userprofile,
                    active=False,
                    referrer = referrer)
                refd.save()
            #send to payment checkout
            return HttpResponseRedirect('https://paystack.com/pay/mockexamsngsubscription')

        else:
            context_instance = {'uform': uform,
             'pform': pform,
              'sform': sform,
              'about':about,
              'referrer': referrer,
              'CURRENTYEAR':CURRENTYEAR,
              'error_message': 'Invalid Registration!'}

            return render(request, 'userprofile/ref_reg_profile.html', context_instance)
    else:
        get_ip(request, 'register')
        uform = UserForm()
        pform = RefUserProfileForm()
        sform = SubjectForm()
        context_instance = {'uform': uform,
             'pform': pform,
              'sform': sform,
              'about':about,
              'referrer': referrer,
              'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'userprofile/ref_reg_profile.html', context_instance)


def ref_bank_reg_profile(request, code):
    if About.objects.all().exists():
        about = About.objects.all()[0]
    else:
        about = None
    get_ip(request, 'referral')
    today = timezone.now().today()
    CURRENTYEAR = today.year
    referrer = Referrer.objects.get(ref_code=code)
    if request.method == 'POST':
        uform = UserForm(request.POST)
        pform = RefUserProfileForm(request.POST, request.FILES)
        sform = SubjectForm(request.POST)
        tform = BankDirectForm(request.POST)
        if uform.is_valid() and pform.is_valid() and sform.is_valid() and tform.is_valid():
            user = uform.save(commit=False)
            # dg = rannum(8)
            # lt = ranlet(2)
            # username = uform.cleaned_data['username']
            password = uform.cleaned_data['password1']
            email = uform.cleaned_data['email']
            user.set_password(password)
            user.save()
            dg = rannum(8)
            lt = ranlet(2)
            regcode = str(dg) + lt
            user.username = regcode
            user.save()

            payment_date = tform.cleaned_data['payment_date']
            amount = tform.cleaned_data['amount']
            bank = tform.cleaned_data['bank']
            depositor_name = tform.cleaned_data['depositor_name']
            transaction_id = tform.cleaned_data['transaction_id']
            payment_mode = tform.cleaned_data['payment_mode']
            subject = sform.cleaned_data['subject']
            userprofile, new = UserProfile.objects.get_or_create(user=user)
            first_name = pform.cleaned_data['first_name']
            surname = pform.cleaned_data['surname']
            exam_area = pform.cleaned_data['exam_area']
            examination = pform.cleaned_data['examination']
            feedback = pform.cleaned_data['feedback']
            course = pform.cleaned_data['course']
            exam_state = pform.cleaned_data['exam_state']
            phone = pform.cleaned_data['phone']
            sex = pform.cleaned_data['sex']
            referral_code = pform.cleaned_data['referral_code']
            passport = pform.cleaned_data['passport']

            userprofile.exam_area = exam_area
            userprofile.first_name = first_name
            userprofile.surname = surname
            userprofile.sex = sex
            userprofile.referral_code = referral_code
            userprofile.examination = examination
            userprofile.feedback = feedback
            userprofile.payment_mode = 'bank'
            userprofile.pin = '0000000000'
            userprofile.serial = 'BANK'
            userprofile.course = course
            userprofile.exam_state = exam_state
            userprofile.paid = False
            for sub in subject:
                userprofile.subject.add(sub)
            userprofile.phone = phone
            userprofile.regnum = regcode
            userprofile.passport = passport
            userprofile.save()

            #bank details
            paying = BankDirect(
                user = userprofile,
                payment_date = payment_date,
                amount = amount,
                bank = bank,
                depositor_name = depositor_name,
                transaction_id = transaction_id,
                payment_mode = payment_mode)
            paying.save()
            #credit referrer
            try:
                referrer = Referrer.objects.get(ref_code=code)
                refd = Referral(
                    user_activated = userprofile,
                    active=False,
                    referrer = referrer)
                refd.save()
            except Referrer.DoesNotExist:
                referrer = Referrer.objects.get(ref_code='Y907')
                refd = Referral(
                    user_activated = userprofile,
                    active=False,
                    referrer = referrer)
                refd.save()
            #send to payment checkout
            messages.add_message(request, messages.INFO, "REGISTRATION SUCCESSFUL! Login With Email.")
            return HttpResponseRedirect('/login/')

        else:
            context_instance = {'uform': uform,
             'pform': pform,
              'sform': sform,
              'tform': tform,
              'about':about,
              'referrer': referrer,
              'CURRENTYEAR':CURRENTYEAR,
              'error_message': 'Invalid Registration!'}

            return render(request, 'userprofile/reg_bank_profile.html', context_instance)
    else:
        get_ip(request, 'register')
        uform = UserForm()
        pform = RefUserProfileForm()
        sform = SubjectForm()
        tform = BankDirectForm()
        context_instance = {'uform': uform,
             'pform': pform,
              'sform': sform,
              'tform': tform,
              'about':about,
              'referrer': referrer,
              'CURRENTYEAR':CURRENTYEAR}
    return render(request, 'userprofile/reg_bank_profile.html', context_instance)
