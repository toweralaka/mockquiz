# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin, messages
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import logout, get_user_model, authenticate, login
from django.utils.html import format_html
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.mail.message import EmailMessage
from django.contrib.auth.decorators import permission_required
from django.contrib.admin import helpers
from django.shortcuts import render
from django.conf.urls import url
from django.utils import timezone
from django.conf import settings
# from django.contrib.auth.models import User
from .forms import WriteForm, UserImportForm, StartExamForm, ResultImportForm
from mngr.forms import SalesForm
from .models import (ExamCenter, UserProfile, Batch, Result, SendResult, Referral, BankDirect,
                        WriteAccess, UserScript, SubjectScore, SpecialCase, ExamArea, State, UserBank)
from bank.models import Topic, Examination, Subject, Question, SubTopic
from mngr.models import AccessCode, Advert
from mngr.views import send_sms, send_bbn_sms
import os
import requests
import csv, StringIO #io


User = get_user_model()


#define custom admin actions here
def export_batch_user(self, request, queryset):
    for btch in queryset:
        # Create the HttpResponse object with the appropriate CSV header.
        file_name = str(btch.exam_center)+'_Batch'+str(btch.number)+'_'+'Users'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Batch_Users.csv"'#"somefilename.csv"'
        writer = csv.writer(response)
        writer.writerow(['user_id', 'username', 'password_hash','profile_id','pin', 'serial', 'first_name', 
                'surname', 'sex', 'phone', 'course', 'passport', 'regnum', 'pc', 'seat', 'online', 'regdate', 
                'give_sample', 'giftpin', 'giftserial', 'batch_id', 'exam_area_id', 'exam_center_id', 'exam_state_id', 
                'examination_id', 'user_id', 'feedback_id', 'paid', 'payment_mode', 'referral_code', 'mails', 'subject'])
        allprofiles = UserProfile.objects.filter(batch=btch)
        for i in allprofiles:
            d_user = i.user
            subject = ""
            for j in i.subject.all():
                subject += (str(j.id)) + ','
            #subjects = ','.join(subject)
            writer.writerow([d_user.id,d_user.username,d_user.password,i.id,i.pin, i.serial, i.first_name, 
                i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, int(i.pc), i.seat, int(i.online), i.regdate, 
                int(i.give_sample), i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, 
                i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, int(i.paid), i.payment_mode, 
                i.referral_code, int(i.mails), subject])
        return response

export_batch_user.short_description = 'Export Batch Users'



def take_offline(modeladmin, request, queryset):
    for pers in queryset:
        pers.online = False
        pers.save()
        message_bit = str(pers.regnum)+" Successfully Taken Offline!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
take_offline.short_description = 'Take Candidate(s) Offline'

def activate_selected(modeladmin, request, queryset):
    for pers in queryset:
        pers.active = True
        pers.save()
        message_bit = str(pers)+" Successfully Activated!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
activate_selected.short_description = 'Activate Selected'

def deactivate_selected(modeladmin, request, queryset):
    for pers in queryset:
        pers.active = False
        pers.save()
        message_bit = str(pers)+" Successfully Deactivated!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
deactivate_selected.short_description = 'Deactivate Selected'


def pay_referrer(modeladmin, request, queryset):
    for pers in queryset:
        if not pers.paid:
            pers.paid = True
            pers.payment_date = timezone.now()
            pers.save()
            message_bit = "Payment Successful For "+str(pers.referrer.ref_code)+"!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
pay_referrer.short_description = 'Pay Referrer'



class SupReferralAdmin(admin.ModelAdmin):
    list_display = ('referral', 'sup_referrer', 'paid', 'payment_date')
    search_fields = ('sup_referrer',)
    list_filter = ('payment_date', 'paid', 'sup_referrer')
    actions = ['pay_referrer',]


    def get_actions(self, request):
        actions = super(SupReferralAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions


def batch_users(modeladmin, request, queryset):
    for examcenter in queryset:
        area = examcenter.exam_area
        state = area.state
        users = UserProfile.objects.filter(exam_center=examcenter)
        
        for userprofile in users:
            b = Batch.objects.filter(exam_center=examcenter).order_by('filled')
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
                        userprofile.seat = btch.filled
                        userprofile.pc = True
                        userprofile.save()
                    else:
                        pass
        message_bit = str(examcenter)+" Candidates Successfully Batched!"
    modeladmin.message_user(request, "%s" % message_bit)                
batch_users.short_description = 'Batch unsorted users'

def show_results(modeladmin, request, queryset):
    for batch in queryset:
        batch.show_result = True
        batch.save()
        
show_results.short_description = 'Show Batch Result'

def hide_results(modeladmin, request, queryset):
    for batch in queryset:
        batch.show_result = False
        batch.save()
        
hide_results.short_description = 'Hide Batch Result'

def send_email(msgsub, msgbody, msgto):
    return requests.post(
        "https://api.mailgun.net/v3/mail.mockexamsng.com/messages",
        auth=("api", "apikey"),
        data={"from": "Mockexamsng <mail.mockexamsng.com>",
              "to": [msgto,],
              "subject": msgsub,
              "text": msgbody})



#@permission_required('batch.send')
def senduserresult(modeladmin, request, queryset):
    for pers in queryset:
        try:
            result = Result.objects.get(user=pers)
        except Result.DoesNotExist:
            pass
        else:
            if result.marked:
                t = result.user.regnum+" MOCK RESULT:"
                for r in result.scores:
                    t = t+str(r)+" "
                mesgbody =  t 
                dphone = int(result.user.phone)
                smesto = '234'+str(dphone)
                #smesto = str(result.user.phone)
                usersend = SendResult.objects.filter(user = str(result.user.regnum))
                if usersend.exists():
                    message_bit = str(result.user.regnum) + " Result Previously Sent!"
                else:
                    try:
                        #send_sms(mesgbody, smesto)
                        send_bbn_sms(mesgbody, smesto)
                    except IndexError:
                        message_bit = "There Is No Result To Send"
                    except Exception:
                        message_bit = (" Result Sending Not Successful for Number "+str(pers.regnum)+
                        ". Check Internet and Send Again")
                    else:
                        message_bit = "Result Sending Successful for Number "+str(pers.regnum)+"!"
                    modeladmin.message_user(request, "%s" % message_bit)
                    sendnew = SendResult(
                        user = str(result.user.regnum),
                        result= result)
                    sendnew.save()

senduserresult.short_description = 'Send User Result'


def confirmpayment(modeladmin, request, queryset):
    for pers in queryset:
        pers.paid=True
        pers.save()
        try:
            bank = BankDirect.objects.get(user=pers)
            bank.confirmed=True
            bank.save()
        except BankDirect.DoesNotExist:
            pass
        try:
            referral = Referral.objects.get(user_activated=pers)
            referral.active = True
            referral.save()
        except Referral.DoesNotExist:
            pass
        else:
            mesgbody =  "Payment Confirmed. Login With Email On Mockexamsng.com" 
            smesto = str(pers.phone)
            try:
                send_sms(mesgbody, smesto)
            except Exception:
                message_bit = " Confirmation message was not sent. Check Internet and Send Again"
            else:
                message_bit = "Confirmation Message Successful for "+str(pers.regnum)+"!"
            modeladmin.message_user(request, "%s" % message_bit)

confirmpayment.short_description = 'Confirm User Payment'


class BatchAdmin(admin.ModelAdmin):
    fields = ('exam_center', 'number', 'exam_period', 'capacity', 'date', 'time', 'show_result', 'active', 'write_exam')
    #readonly_fields = ('exam_center', 'number', 'capacity', 'date', 'time', 'show_result', 'active')
    list_display = ('exam_center', 'number', 'capacity', 'qty', 'date', 'time', 'write_exam', 'show_result',)# 'batch_actions')
    search_fields = ('exam_center__name', )
    list_filter = ('active', 'show_result', 'write_exam')
    actions = ['sendresults', 'export_results', 'activate_client', show_results, 
    hide_results, export_batch_user, activate_selected, deactivate_selected]

    def get_urls(self):
        urls = super(BatchAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^write/$',
                self.admin_site.admin_view(self.write),
                name='userprofile_batch_write',
            ),
            url(
                r'^activate/$',
                self.admin_site.admin_view(self.activate),
                name='userprofile_batch_activate',
            ),
        ]
        return custom_urls + urls


    def get_actions(self, request):
        actions = super(BatchAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'sendresults' in actions:
                del actions['sendresults']
            if 'show_results' in actions:
                del actions['show_results']
            if 'hide_results' in actions:
                del actions['hide_results']
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions



    def write(self, request):
        context = {
            'title': 'ACTIVATE BATCH',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = WriteForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                password = form.cleaned_data['password']
                if not WriteAccess.objects.filter(name=name, password=password).exists():
                    error_message = 'Invalid name and password combination!'
                    context['error_message'] = error_message
                    form = WriteForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/userprofile/batch/writeexam.html', context)
                else:
                    access = WriteAccess.objects.get(name=name, password=password)
                    if access.active == False:
                        error_message = 'This access is inactive!'
                        context['error_message'] = error_message
                        form = WriteForm()
                        context['form'] = form
                        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                                 self.get_prepopulated_fields(request))
                        return render(request, 'admin/userprofile/batch/writeexam.html', context)
                    else:
                        passs = password[0:5]
                        access = WriteAccess.objects.get(name=name, password=password)
                        bch = access.batch
                        batch = bch.id
                        dbatch = Batch.objects.get(id=batch)
                        centr = dbatch.exam_center
                        allbatch = Batch.objects.filter(exam_center=centr)
                        if str(passs) == 'mopup':
                            for i in allbatch:
                                i.write_exam = True
                                i.save()
                                profiles = UserProfile.objects.filter(batch=i)

                                for up in profiles:
                                    try:
                                        checkresult = Result.objects.get(user=up)
                                    except Exception:
                                        duser = User.objects.get(username=up.user)
                                        try:
                                            duser.username=up.regnum
                                            duser.save()
                                        except Exception:
                                            pass
                                        userscript = UserScript.objects.filter(user=up)
                                        for i in userscript:
                                            i.delete()
                                        subjects = up.subject.all()
                                        exam = up.examination
                                        for subject in subjects:    
                                            if subject.topic_set.all().exists():
                                                topics = subject.topic_set.all().order_by('?')
                                                for tp in topics:
                                                    subtops = tp.subtopic_set.all().order_by('?')
                                                    if tp.subtopic_set.all().exists():
                                                        subtpunit = 0
                                                        for i in subtops:
                                                            if subtpunit < int(tp.unit_subtopic):
                                                                que_set = Question.objects.filter(examination=str(exam), 
                                                                    subject=str(subject.name), 
                                                                    topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                                bulk_script = []
                                                                for ques in que_set:
                                                                    new_script = UserScript()
                                                                    new_script.question = ques
                                                                    new_script.user = up
                                                                    bulk_script.append(new_script)
                                                                UserScript.objects.bulk_create(bulk_script)
                                                                subtpunit += 1
                                                            else:
                                                                pass
                                                    else:
                                                        que_set = Question.objects.filter(examination=str(exam), 
                                                            subject=str(subject.name), 
                                                            topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                        bulk_script = []
                                                        for ques in que_set:
                                                            new_script = UserScript()
                                                            new_script.question = ques
                                                            new_script.user = up
                                                            bulk_script.append(new_script)
                                                        UserScript.objects.bulk_create(bulk_script)
                                            else:
                                                que_set = Question.objects.filter(examination=str(exam), 
                                                    
                                                    subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                                bulk_script = []
                                                for ques in que_set:
                                                    new_script = UserScript()
                                                    new_script.question = ques
                                                    new_script.user = up
                                                    bulk_script.append(new_script)
                                                UserScript.objects.bulk_create(bulk_script)
                                                    # sesques = UserScript(
                                                    #     user = up,
                                                    #     question = str(ques.id))
                                                    # sesques.save()
                            message_bit = "ALL BATCHES ACTIVATED!"
                        else:
                            for i in allbatch:
                                i.write_exam = False
                                i.save()
                            access = WriteAccess.objects.get(name=name, password=password)
                            bch = access.batch
                            batch = bch.id
                            dbatch = Batch.objects.get(id=batch)
                            dbatch.write_exam = True
                            dbatch.save()
                            profiles = UserProfile.objects.filter(batch__id=dbatch.id)
                            for up in profiles:
                                try:
                                    checkresult = Result.objects.get(user=up)
                                except Exception:
                                    duser = User.objects.get(username=up.user)
                                    if d_user.username != up.regnum:
                                        try:
                                            duser.username=up.regnum
                                            duser.save()
                                        except Exception:
                                            pass
                                    userscript = UserScript.objects.filter(user=up)
                                    for i in userscript:
                                        i.delete()
                                    subjects = up.subject.all()
                                    exam = up.examination
                                    for subject in subjects:    
                                        if subject.topic_set.all().exists():
                                            topics = subject.topic_set.all()
                                            for tp in topics:
                                                subtops = tp.subtopic_set.all()
                                                if tp.subtopic_set.all().exists():
                                                    subtpunit = 0
                                                    for i in subtops:
                                                        if subtpunit < int(tp.unit_subtopic):
                                                            que_set = Question.objects.filter(examination=str(exam), 
                                                                subject=str(subject.name), 
                                                                topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                            bulk_script = []
                                                            for ques in que_set:
                                                                new_script = UserScript()
                                                                new_script.question = ques
                                                                new_script.user = up
                                                                bulk_script.append(new_script)
                                                            UserScript.objects.bulk_create(bulk_script)
                                                            subtpunit += 1
                                                        else:
                                                            pass
                                                else:
                                                    que_set = Question.objects.filter(examination=str(exam), 
                                                        subject=str(subject.name), 
                                                        topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                    bulk_script = []
                                                    for ques in que_set:
                                                        new_script = UserScript()
                                                        new_script.question = ques
                                                        new_script.user = up
                                                        bulk_script.append(new_script)
                                                    UserScript.objects.bulk_create(bulk_script)
                                        else:
                                            que_set = Question.objects.filter(examination=str(exam), 
                                                
                                                subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                            bulk_script = []
                                            for ques in que_set:
                                                new_script = UserScript()
                                                new_script.question = ques
                                                new_script.user = up
                                                bulk_script.append(new_script)
                                            UserScript.objects.bulk_create(bulk_script)
                            message_bit = 'BATCH '+str(dbatch)+' IS ACTIVATED!'
                        self.message_user(request, "%s" % message_bit)

            else:
                form = WriteForm(request.POST)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/batch/writeexam.html', context)
        form = WriteForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/batch/writeexam.html', context)


    def export_results(self, request, queryset):

        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

# for i in allprofiles:
#             d_user = i.user
#             subjects = []
#             for j in i.subject.all():
#                 subjects.append(int(j.id))
#             writer.writerow([d_user.id,d_user.username,d_user.password,i.id,i.pin, i.serial, i.first_name, 
#                 i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, i.pc, i.seat, i.online, i.regdate, 
#                 i.give_sample, i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, 
#                 i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, i.paid, i.payment_mode, 
#                 i.referral_code, i.mails, subjects])
            
            writer = csv.writer(attachment_csv_file)

            writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user', 'done', 'duration', 'time_ended'])
            reslt = Result.objects.filter(batch=btch)
            users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user', 'done', 'duration', 'time_ended')
            for i in users:
                # pers = i.user.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, 
                #profl.marked, profl.total,)
                writer.writerow(i)

            email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach subject scores
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['subject', 'score', 'user'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                uscores = SubjectScore.objects.filter(user=str(pf.regnum))
                scores = uscores.values_list('subject', 'score', 'user')
                for i in scores:
                    writer.writerow(i)

            email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
            'text/csv')

            # #attach special cases
            # attachment_csv_file = StringIO.StringIO()

            # writer = csv.writer(attachment_csv_file)

            # writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            # profiles = UserProfile.objects.filter(batch=btch)
            # for pf in profiles:
            #     case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
            #     cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
            #     for i in cases:
            #         writer.writerow(i)

            # email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            # 'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception:
                message_bit = ("Export Not Successful for " + str(btch.exam_center) +" Batch"+
                str(btch.number)+". Check Internet and Export Again")
            else:
                message_bit = "Export Successful for " + str(btch.exam_center) +" Batch"+str(btch.number)+"!"
            self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export Result'


    #@permission_required('batch.send')
    def sendresults(self, request, queryset):
        for btch in queryset:
            users = UserProfile.objects.filter(batch=btch)
            for pers in users:
                try:
                    result = Result.objects.get(user=pers)
                except Result.DoesNotExist:
                    pass
                else:
                    if result.marked:
                        t = result.user.regnum+" MOCK RESULT:"
                        for r in result.scores:
                            t = t+str(r)+" "
                        mesgbody =  t 
                        smesto = str(result.user.phone)
                        usersend = SendResult.objects.filter(user = str(result.user.regnum))
                        if usersend.exists():
                            message_bit = str(result.user.regnum) + " result previously sent!"
                        else:
                            try:
                                send_sms(mesgbody, smesto)
                            except Exception as e:
                                message_bit = (" Result Sending Not Successful for Number "+str(pers.regnum)+
                                ". Check Internet and Send Again")
                            else:
                                message_bit = "Result Sending Successful for Number "+str(pers.regnum)+"!"
                                sendnew = SendResult(
                                user = str(result.user.regnum),
                                result= result)
                                sendnew.save()
                        self.message_user(request, "%s" % message_bit)
                        

    sendresults.short_description = 'Send Mock Result'


    def activate_batch(self, request, queryset):
        context = {
            'title': 'ACTIVATE BATCH',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        form = WriteForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/batch/writeexam.html', context)
    activate_batch.short_description = 'Activate Batch'



    def activate(self, request):
        qty = 0
        context = {
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = WriteForm(request.POST)
            if form.is_valid():
                passcode = form.cleaned_data['name']
                password = form.cleaned_data['password']
                if str(password) == 'malady':
                    dcards = AccessCode.objects.filter(passcode=passcode)
                    for i in dcards:
                        try:
                            userp = UserProfile.objects.get(serial=i.srn, pin=i.pin)#, batch=btch)##btch may or may not be filtered
                        except UserProfile.DoesNotExist:
                            pass
                        else:
                            userr = User.objects.get(username=userp.user)
                            userr.is_active = True
                            userr.save()
                            qty += 1
                    message_bit = "ACTIVATE SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    context['qty'] = qty
                    return render(request, 'admin/userprofile/batch/activate_client.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                form = WriteForm(request.POST)
                context['form'] = form
                context['title'] = 'ACTIVATE CLIENT'
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/batch/activate_client.html', context)
        form = WriteForm()
        context['form'] = form
        context['title'] = 'ACTIVATE CLIENT'
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/batch/activate_client.html', context)
    


    def activate_client(self, request, queryset):
        context = {
            'title': 'ACTIVATE CLIENT',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = WriteForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/batch/activate_client.html', context)
    activate_client.short_description = 'Activate Client'


def reset_questions(modeladmin, request, queryset):
    for pers in queryset:
        exam = pers.examination
        subjects = pers.subject.all()
        userques = UserScript.objects.filter(user = pers)
        #clear the userscripts
        for i in userques:
            i.delete()
        #clear the results
        try:
            result = Result.objects.get(user=pers)
            result.duration = 0
            result.total = 0.0
            result.done = False
            result.marked = False
            result.timestamp = timezone.localtime(timezone.now())
            result.save()
        except Result.DoesNotExist:
            pass
        #clear the subject scores
        for i in SubjectScore.objects.filter(user=str(pers.regnum)):
            i.delete()
        #create new userscripts
        for subject in subjects:
            topics = subject.topic_set.all()
            if subject.topic_set.all().exists():
                for tp in topics:
                    subtops = tp.subtopic_set.all()
                    if tp.subtopic_set.all().exists():
                        subtpunit = 0
                        for i in subtops:
                            if subtpunit < int(tp.unit_subtopic):
                                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                bulk_script = []
                                for ques in que_set:
                                    new_script = UserScript()
                                    new_script.question = ques
                                    new_script.user = pers
                                    bulk_script.append(new_script)
                                UserScript.objects.bulk_create(bulk_script)
                                subtpunit += 1
                            else:
                                pass
                    else:
                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                        bulk_script = []
                        for ques in que_set:
                            new_script = UserScript()
                            new_script.question = ques
                            new_script.user = pers
                            bulk_script.append(new_script)
                        UserScript.objects.bulk_create(bulk_script)
                            
            else:
                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                bulk_script = []
                for ques in que_set:
                    new_script = UserScript()
                    new_script.question = ques
                    new_script.user = pers
                    bulk_script.append(new_script)
                UserScript.objects.bulk_create(bulk_script)
        message_bit = str(pers.regnum)+" Questions Successfully Reset!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
reset_questions.short_description = 'Reset Candidate(s) Questions'

class ScriptStack(admin.TabularInline):
    model = UserScript
    fields = ('dsubject', 'choice', 'realans')
    readonly_fields = ('realans', 'dsubject') #this allows property to be included in fields

    def has_delete_permission(self, request, obj=None):
        # Disable delete
        return False

    def has_add_permission(self, request, obj=None):
        # Disable delete
        return False

class ResultStack(admin.TabularInline):
    model = Result
    fields = ('marked',)

    def has_delete_permission(self, request, obj=None):
        # Disable delete
        return False

    def has_add_permission(self, request, obj=None):
        # Disable delete
        return False


class UserProfileAdmin(admin.ModelAdmin):
    # inlines = [
    #     ResultStack,
    #     ScriptStack,
        
    # ]
    list_display = ('user', 'result_score', 'referral_code', 'first_name', 'surname', 'buyer', 'phone', 'examination', 
        'exam_area', 'taken_test', 'seat', 'image_tag')
    # list_display = ('user', 'paid', 'referral_code', 'first_name', 'subss', 'surname', 'buyer', 'phone', 'examination', 
    #     'exam_area', 'batch', 'image_tag','pc', 'taken_test')
    readonly_fields = ('image_tag',)
    search_fields = ('regnum', 'surname', 'first_name', 'serial', 'phone')
    list_filter = ('regdate', 'examination', 'exam_area', 'exam_center', 'batch', 'feedback', 'payment_mode', 'paid')
    # fields = ('first_name', 'subject', 'online')
    # fields = ('user', 'online')
    actions = ['print_photo_album', 'deactivate_user', 'activate_user', 'export_users',
        senduserresult, confirmpayment, take_offline, reset_questions]

    def get_urls(self):
        urls = super(UserProfileAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^deactivate/$',
                self.admin_site.admin_view(self.deactivate),
                name='userprofile_userprofile_deactivate',
            ),
            url(
                r'^activate/$',
                self.admin_site.admin_view(self.activate),
                name='userprofile_userprofile_activate',
            ),
            url(
                r'^addusers/$',
                self.admin_site.admin_view(self.addusers),
                name='userprofile_userprofile_addusers',
            ),
            url(
                r'^startexam/$',
                self.admin_site.admin_view(self.startexam),
                name='userprofile_userprofile_startexam',
            ),
            url(
                r'^importresults/$',
                self.admin_site.admin_view(self.importresults),
                name='userprofile_userprofile_importresults',
            ),

        ]
        return custom_urls + urls

    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            # if 'print_photo_album' in actions:
            #     del actions['print_photo_album']
            if 'confirmpayment' in actions:
                del actions['confirmpayment']
            if 'senduserresult' in actions:
                del actions['senduserresult']
            if 'delete_selected' in actions:
                del actions['delete_selected']
            if 'export_users' in actions:
                del actions['export_users']
        return actions

    def addusers(self, request):
        context = {
            'title': 'IMPORT USERS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = UserImportForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                name = form.cleaned_data['file_name']
                dfile = UserBank.objects.get(file_name=name)
                parturl = dfile.user_file
                fileurl = os.path.join(settings.MEDIA_ROOT, str(parturl))
                with open(str(fileurl)) as f:
                    reader = csv.reader(f)
                    for row in reader:
                #         writer.writerow([d_user.id,d_user.username,d_user.password,i.id,i.pin, i.serial, i.first_name, 
                # i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, int(i.pc), i.seat, int(i.online), i.regdate, 
                # int(i.give_sample), i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, 
                # i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, int(i.paid), i.payment_mode, 
                # i.referral_code, int(i.mails), subject])
                        try:
                            user = User.objects.get(username=row[1])
                        except User.DoesNotExist:
                            try:
                                user = User.objects.create(id=row[0], username=row[1], password=row[2])
                                try:
                                    profile = UserProfile.objects.get(user=user, id=row[3])
                                except UserProfile.DoesNotExist:
                                    try:
                                        profile = UserProfile(
                                            id = row[3],
                                            user = user,
                                            pin = row[4], 
                                            serial = row[5], 
                                            first_name = row[6], 
                                            surname = row[7], 
                                            sex = row[8], 
                                            phone = row[9], 
                                            course = row[10], 
                                            passport = row[11], 
                                            regnum = row[12], 
                                            pc = row[13],  
                                            online = row[15], 
                                            regdate = row[16], 
                                            give_sample = row[17], 
                                            giftpin = row[18], 
                                            giftserial = row[19]
                                            )
                                        profile.save()
                                    except Exception:
                                        pass
                                    else:
                                        try:
                                            profile.seat = int(row[14])
                                        except Exception:
                                            pass
                                        try:
                                            profile.batch_id = Batch.objects.get(id=row[20])
                                        except Exception:
                                            pass
                                        try:
                                            profile.exam_area_id = ExamArea.objects.get(id=row[21])
                                        except Exception:
                                            pass
                                        try:
                                            profile.exam_center_id = ExamCenter.objects.get(id=row[22]) 
                                        except Exception:
                                            pass
                                        try:
                                            profile.exam_state_id = State.objects.get(id=row[23]) 
                                        except Exception:
                                            pass
                                        try:
                                            profile.examination_id = Examination.objects.get(id=row[24]) 
                                        except Exception:
                                            pass
                                        try:
                                            profile.feedback_id = Advert.objects.get(id=row[26]) 
                                        except Exception:
                                            pass
                                        profile.paid = row[27] 
                                        profile.payment_mode = row[28] 
                                        profile.referral_code = row[29] 
                                        profile.mails = row[30]
                                        all_subjs = (row[31]).split(',')
                                        for subj in all_subjs:#row[31]:
                                            try:
                                                profile.subject.add(subj)
                                            except Exception:
                                                pass
                                        profile.save()
                            except Exception:
                                pass                    
                        
                    message_bit = "UPLOAD SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    form = UserImportForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/userprofile/userprofile/add_users.html', context)
            else:
                message_bit = "INVALID UPLOAD!"
                self.message_user(request, "%s" % message_bit)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/userprofile/add_users.html', context)
        else:
            form = UserImportForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/userprofile/userprofile/add_users.html', context)

    def startexam(self, request):
        context = {
            'title': 'START EXAM',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = StartExamForm(request.POST)
            if form.is_valid():
                center = form.cleaned_data['exam_center']
                batch = form.cleaned_data['batch']
                password = form.cleaned_data['password']
                mngr = authenticate(username=request.user.username, password=password)
                if mngr is None:
                    message_bit = "INVALID!"
                    form = StartExamForm()
                    context['form'] = form
                    self.message_user(request, "%s" % message_bit, level=messages.ERROR)
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/userprofile/userprofile/writeexam.html', context)
                else:
                    centr =  ExamCenter.objects.get(id=center)
                    allbatch = Batch.objects.filter(exam_center=centr)
                    if batch == 'all':
                        for i in Batch.objects.all():
                            i.write_exam = False
                            i.save()
                        for i in allbatch:
                            i.write_exam = True
                            i.save()
                            profiles = UserProfile.objects.filter(batch=i)
                            for up in profiles:
                                #check if user has attempted exam
                                try:
                                    checkresult = Result.objects.get(user=up)
                                except Result.DoesNotExist:
                                    userscript = UserScript.objects.filter(user=up)
                                    for i in userscript:
                                        i.delete()
                                    subjects = up.subject.all()
                                    exam = up.examination
                                    for subject in subjects:    
                                        if subject.topic_set.all().exists():
                                            topics = subject.topic_set.all().order_by('?')
                                            for tp in topics:
                                                subtops = tp.subtopic_set.all().order_by('?')
                                                if tp.subtopic_set.all().exists():
                                                    subtpunit = 0
                                                    for i in subtops:
                                                        if subtpunit < int(tp.unit_subtopic):
                                                            que_set = Question.objects.filter(examination=str(exam), 
                                                                subject=str(subject.name), 
                                                                topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                            bulk_script = []
                                                            for ques in que_set:
                                                                new_script = UserScript()
                                                                new_script.question = ques
                                                                new_script.user = up
                                                                bulk_script.append(new_script)
                                                            UserScript.objects.bulk_create(bulk_script)
                                                            subtpunit += 1
                                                        else:
                                                            pass
                                                else:
                                                    que_set = Question.objects.filter(examination=str(exam), 
                                                        subject=str(subject.name), 
                                                        topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                    bulk_script = []
                                                    for ques in que_set:
                                                        new_script = UserScript()
                                                        new_script.question = ques
                                                        new_script.user = up
                                                        bulk_script.append(new_script)
                                                    UserScript.objects.bulk_create(bulk_script)

                                        else:
                                            que_set = Question.objects.filter(examination=str(exam), 
                                                subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                            bulk_script = []
                                            for ques in que_set:
                                                new_script = UserScript()
                                                new_script.question = ques
                                                new_script.user = up
                                                bulk_script.append(new_script)
                                            UserScript.objects.bulk_create(bulk_script)
                        message_bit = "ALL BATCHES ACTIVATED!"
                    else:
                        dbatch =  Batch.objects.get(id=batch)
                        for i in Batch.objects.all():
                            i.write_exam = False
                            i.save()
                        dbatch.write_exam = True
                        dbatch.save()
                        profiles = UserProfile.objects.filter(batch__id=dbatch.id)
                        for up in profiles:
                            try:
                                checkresult = Result.objects.get(user=up)
                            except Result.DoesNotExist:
                                #delete old scripts
                                userscript = UserScript.objects.filter(user=up)
                                for i in userscript:
                                    i.delete()
                                #create new scripts
                                subjects = up.subject.all()
                                exam = up.examination
                                for subject in subjects:    
                                    if subject.topic_set.all().exists():
                                        topics = subject.topic_set.all()
                                        for tp in topics:
                                            subtops = tp.subtopic_set.all()
                                            if tp.subtopic_set.all().exists():
                                                subtpunit = 0
                                                for i in subtops:
                                                    if subtpunit < int(tp.unit_subtopic):
                                                        que_set = Question.objects.filter(examination=str(exam), 
                                                            subject=str(subject.name), 
                                                            topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                        bulk_script = []
                                                        for ques in que_set:
                                                            new_script = UserScript()
                                                            new_script.question = ques
                                                            new_script.user = up
                                                            bulk_script.append(new_script)
                                                        UserScript.objects.bulk_create(bulk_script)
                                                        subtpunit += 1
                                                    else:
                                                        pass
                                            else:
                                                que_set = Question.objects.filter(examination=str(exam), 
                                                    subject=str(subject.name), 
                                                    topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                bulk_script = []
                                                for ques in que_set:
                                                    new_script = UserScript()
                                                    new_script.question = ques
                                                    new_script.user = up
                                                    bulk_script.append(new_script)
                                                UserScript.objects.bulk_create(bulk_script)
                                    else:
                                        que_set = Question.objects.filter(examination=str(exam), 
                                            
                                            subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                        bulk_script = []
                                        for ques in que_set:
                                            new_script = UserScript()
                                            new_script.question = ques
                                            new_script.user = up
                                            bulk_script.append(new_script)
                                        UserScript.objects.bulk_create(bulk_script)
                        message_bit = 'BATCH '+str(dbatch)+' IS ACTIVATED!'
                    self.message_user(request, "%s" % message_bit)

            else:
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/userprofile/writeexam.html', context)
        form = StartExamForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/userprofile/writeexam.html', context)


    def importresults(self, request):
        context = {
            'title': 'IMPORT RESULTS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = ResultImportForm(request.POST, request.FILES)
            if form.is_valid():
                result_file_name = form.cleaned_data['result_file_name']
                result_file = form.cleaned_data['result_file']
                scores_file_name = form.cleaned_data['scores_file_name']
                scores_file = form.cleaned_data['scores_file']
                try:
                    results = UserBank.objects.create(user_file=result_file, file_name=result_file_name)
                    scores = UserBank.objects.create(user_file=scores_file, file_name=scores_file_name)
                except Exception:
                    message_bit = "INVALID UPLOAD!"
                    self.message_user(request, "%s" % message_bit)
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                            self.get_prepopulated_fields(request))
                    return render(request, 'admin/userprofile/userprofile/add_results.html', context)
                else:
                    # form.save()
                    dresultfile = UserBank.objects.get(file_name=result_file_name)
                    dscoresfile = UserBank.objects.get(file_name=scores_file_name)
                    resultparturl = dresultfile.user_file
                    resultfileurl = os.path.join(settings.MEDIA_ROOT, str(resultparturl))
                    with open(str(resultfileurl)) as f:
                        resultreader = csv.reader(f)
                        for row in resultreader:
                            #  writer1.writerow(['id', 'exam_area_id', 'exam_center_id', 'batch_id', 'timestamp', 'started', 
                            # 'time_ended', 'done', 'marked', 'total','duration', 'user_id', 'timelog'])
                            try:
                                user_reslt = Result.objects.get(id=row[0])
                            except Result.DoesNotExist:
                                try:
                                    user_reslt = Result(
                                        id = row[0],
                                        user = row[11],
                                        timestamp = row[4],
                                        started = row[5],
                                        time_ended = row[6],
                                        done = row[7],
                                        marked = row[8],
                                        total = row[9],
                                        duration = row[10],
                                        timelog = row[12]
                                    )
                                    user_reslt.save()
                                    try:
                                        user_reslt.batch_id = Batch.objects.get(id=row[3])
                                    except Exception:
                                        pass
                                    try:
                                        user_reslt.exam_area_id = ExamArea.objects.get(id=row[1])
                                    except Exception:
                                        pass
                                    try:
                                        user_reslt.exam_center_id = ExamCenter.objects.get(id=row[2]) 
                                    except Exception:
                                        pass
                                    user_reslt.save()
                                except Exception:
                                    pass
                    scoreparturl = dscoresfile.user_file
                    scorefileurl = os.path.join(settings.MEDIA_ROOT, str(scoreparturl))
                    with open(str(scorefileurl)) as v:
                        scorereader = csv.reader(v)
                        for row in scorereader:
                            #writer2.writerow(['id', 'subject', 'score', 'user_reg'])
                            try:
                                user_sc = SubjectScore.objects.get(id=row[0])
                            except SubjectScore.DoesNotExist:
                                try:
                                    user_sc =SubjectScore.objects.create(id=row[0], subject=row[1], score=row[2], user=row[3])
                                except Exception:
                                    pass     
                        message_bit = "UPLOAD SUCCESSFUL!"
                        self.message_user(request, "%s" % message_bit)
                        form = ResultImportForm()
                        context['form'] = form
                        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                                self.get_prepopulated_fields(request))
                        return render(request, 'admin/userprofile/userprofile/add_results.html', context)
            else:
                message_bit = "INVALID UPLOAD!"
                self.message_user(request, "%s" % message_bit)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/userprofile/add_results.html', context)
        else:
            form = ResultImportForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/userprofile/userprofile/add_results.html', context)


    def print_photo_album(self, request, queryset):
        titled = queryset[0]
        context_instance={'profiles':queryset,
        'app_label': self.model._meta.app_label,
        'opts': self.model._meta,
        'has_change_permission': self.has_change_permission(request),
         'titled':titled}
        return render(request,
                          'admin/userprofile/userprofile/album.html',
                          context_instance)
    print_photo_album.short_description = 'Print Photo-Album'

    def export_users(self, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Mock_Users.csv"'#"somefilename.csv"'
        writer = csv.writer(response)
        # writer.writerow(['user_id', 'username', 'password_hash','profile_id','pin', 'serial', 'first_name', 
        #         'surname', 'sex', 'phone', 'course', 'passport', 'regnum', 'pc', 'seat', 'online', 'regdate', 
        #         'give_sample', 'giftpin', 'giftserial', 'batch_id', 'exam_area_id', 'exam_center_id', 'exam_state_id', 
        #         'examination_id', 'user_id', 'feedback_id', 'paid', 'payment_mode', 'referral_code', 'mails', 'subject'])
        for i in queryset:
            d_user = i.user
            subject = ""
            for j in i.subject.all():
                subject += (str(j.id)) + ','
            #subjects = ','.join(subject)
            writer.writerow([d_user.id,d_user.username,d_user.password,i.id,i.pin, i.serial, i.first_name, 
                i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, int(i.pc), i.seat, int(i.online), i.regdate, 
                int(i.give_sample), i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, 
                i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, int(i.paid), i.payment_mode, 
                i.referral_code, int(i.mails), subject])
        return response

    export_users.short_description = 'Export Users'

    def deactivate(self, request):
        qty = 0
        nil = []
        context = {
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = SalesForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                finish = form.cleaned_data['finish']
                buyer = form.cleaned_data['buyer']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    if AccessCode.objects.filter(buyer=buyer).exists():
                        allcards = AccessCode.objects.filter(buyer=buyer)
                        for i in allcards:
                            try:
                                userp = UserProfile.objects.get(serial=str(i.srn))
                            except UserProfile.DoesNotExist:
                                pass
                            else:
                                userr = User.objects.get(username=userp.user)
                                userr.is_active = False
                                userr.save()
                                qty += 1
                        message_bit = "DEACTIVATE SUCCESSFUL!"
                    else:
                        try:
                            first = start[3:8]
                            cardnum = int(first)
                            last = finish[3:8]
                            lastnum = int(last) + 1
                        except Exception as e:
                            message_bit = "THE CARDS ARE INVALID!"
                        else:
                            while cardnum < lastnum:
                                serial = 'MCK' + (str(cardnum))
                                if not AccessCode.objects.filter(srn=serial).exists():
                                    cardnum += 1
                                    nil.append(serial)
                                else:
                                    userp = UserProfile.objects.get(serial=serial)
                                    userr = User.objects.get(username=userp.user)
                                    userr.is_active = False
                                    userr.save()
                                    cardnum += 1
                                    qty += 1
                            message_bit = "DEACTIVATE SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    context['qty'] = qty
                    context['nil'] = nil
                    return render(request, 'admin/userprofile/userprofile/deactivate.html', context)
                else:
                    logout(request)
                return HttpResponseRedirect('/')

            else:
                form = SalesForm(request.POST)
                context['form'] = form
                context['title'] = 'DEACTIVATE USERS'
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/userprofile/deactivate.html', context)
        form = SalesForm()
        context['form'] = form
        context['title'] = 'DEACTIVATE USERS'
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/userprofile/deactivate.html', context)
    
    
    def deactivate_user(self, request, queryset):
        context = {
            'title': 'DEACTIVATE USERS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = SalesForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/userprofile/deactivate.html', context)
    deactivate_user.short_description = 'Deactivate Users'



    def activate(self, request):
        qty = 0
        nil = []
        context = {
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = SalesForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                finish = form.cleaned_data['finish']
                buyer = form.cleaned_data['buyer']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    if AccessCode.objects.filter(buyer=buyer).exists():
                        allcards = AccessCode.objects.filter(buyer=buyer)
                        for i in allcards:
                            try:
                                userp = UserProfile.objects.get(serial=str(i.srn))
                            except UserProfile.DoesNotExist:
                                pass
                            else:
                                userr = User.objects.get(username=userp.user)
                                userr.is_active = True
                                userr.save()
                                qty += 1
                        message_bit = "ACTIVATE SUCCESSFUL!"
                    else:
                        try:
                            first = start[3:8]
                            cardnum = int(first)
                            last = finish[3:8]
                            lastnum = int(last) + 1
                        except Exception as e:
                            message_bit = "THE CARDS ARE INVALID!"
                        else:
                            first = start[3:8]
                            cardnum = int(first)
                            last = finish[3:8]
                            lastnum = int(last) + 1
                            while cardnum < lastnum:
                                serial = 'MCK' + (str(cardnum))
                                if not AccessCode.objects.filter(srn=serial).exists():
                                    cardnum += 1
                                    nil.append(serial)
                                else:
                                    userp = UserProfile.objects.get(serial=serial)
                                    userr = User.objects.get(username=userp.user)
                                    userr.is_active = True
                                    userr.save()
                                    cardnum += 1
                                    qty += 1
                            message_bit = "ACTIVATE SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    context['qty'] = qty
                    context['nil'] = nil
                    return render(request, 'admin/userprofile/userprofile/activate.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                form = SalesForm(request.POST)
                context['form'] = form
                context['title'] = 'ACTIVATE USERS'
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/userprofile/userprofile/activate.html', context)
        form = SalesForm()
        context['form'] = form
        context['title'] = 'ACTIVATE USERS'
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/userprofile/activate.html', context)
    


    def activate_user(self, request, queryset):
        context = {
            'title': 'ACTIVATE USERS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = SalesForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/userprofile/userprofile/activate.html', context)
    activate_user.short_description = 'Activate Users'



def referrerpaid(modeladmin, request, queryset):
    for pers in queryset:
        pers.paid=True
        pers.payment_date = timezone.now()
        pers.save()
        message_bit = "Confirmation of Payment Successful for "+str(pers.user_activated.regnum)+"!"
        modeladmin.message_user(request, "%s" % message_bit)

referrerpaid.short_description = 'Paid The Referrer'


class ReferralAdmin(admin.ModelAdmin):
    fields = ('user_activated',)
    list_display = ('user_activated', 'referrer', 'active', 'paid', 'payment_date')
    search_fields = ('referrer__ref_code',)
    list_filter = ('paid', 'active')
    actions = [referrerpaid, ]



def export_result(self, request, queryset):
    for btch in queryset:
        email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
            ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

        #attach results
        attachment_csv_file = StringIO.StringIO()        
        writer = csv.writer(attachment_csv_file)

        writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user', 'done', 'duration', 'time_ended'])
        reslt = Result.objects.filter(batch=btch)
        users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user', 'done', 'duration', 'time_ended')
        for i in users:
            # pers = i.user.user
            # profl = Result.objects.get(user=pers)
            # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, 
            #profl.marked, profl.total,)
            writer.writerow(i)

        email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
        'text/csv')

        #attach subject scores
        attachment_csv_file = StringIO.StringIO()

        writer = csv.writer(attachment_csv_file)

        writer.writerow(['subject', 'score', 'user'])
        profiles = UserProfile.objects.filter(batch=btch)
        for pf in profiles:
            uscores = SubjectScore.objects.filter(user=str(pf.regnum))
            scores = uscores.values_list('subject', 'score', 'user')
            for i in scores:
                writer.writerow(i)

        email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
        'text/csv')

        # #attach special cases
        # attachment_csv_file = StringIO.StringIO()

        # writer = csv.writer(attachment_csv_file)

        # writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
        # profiles = UserProfile.objects.filter(batch=btch)
        # for pf in profiles:
        #     case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
        #     cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
        #     for i in cases:
        #         writer.writerow(i)

        # email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
        # 'text/csv')
        try:
            email.send(fail_silently=False)
        except Exception:
            message_bit = ("Export Not Successful for " + str(btch.exam_center) +" Batch"+
            str(btch.number)+". Check Internet and Export Again")
        else:
            message_bit = "Export Successful for " + str(btch.exam_center) +" Batch"+str(btch.number)+"!"
        self.message_user(request, "%s" % message_bit)
        
export_result.short_description = 'Export Result'

def export_results(self, request, queryset):   
    #attach results
    attachment_csv_file1 = StringIO.StringIO()
    writer1 = csv.writer(attachment_csv_file1)
    #attach subject scores
    attachment_csv_file2 = StringIO.StringIO()
    writer2 = csv.writer(attachment_csv_file2)
    #insert header
    writer1.writerow(['id', 'exam_area_id', 'exam_center_id', 'batch_id', 'timestamp', 'started', 
            'time_ended', 'done', 'marked', 'total','duration', 'user_regnum', 'timelog'])
    writer2.writerow(['id', 'subject', 'score', 'user_reg'])

    for user in queryset:
        user.save()
        if user.marked:
            candidate = UserProfile.objects.get(regnum=user.user.regnum)
            writer1.writerow([user.id, user.exam_area.id, user.exam_center.id, user.batch.id, user.timestamp, 
                int(user.started), user.time_ended, int(user.done), int(user.marked), 
                user.total, user.duration, user.user.regnum, user.timelog])
            for score in SubjectScore.objects.filter(user=user.user.regnum):
                writer2.writerow([score.id, score.subject, score.score, score.user])
    d_center = queryset[0].user.exam_center
    email = EmailMessage(str(request.user) + ' ' + str(d_center) + ' Results', ' ', 'mockexamsng@gmail.com',
            ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])
    email.attach('attachment_result.csv', attachment_csv_file1.getvalue(),
        'text/csv')
    email.attach('attachment_score.csv', attachment_csv_file2.getvalue(),
        'text/csv')
    try:
        email.send(fail_silently=False)
    except Exception:
        message_bit = ("Export Not Successful, Check Internet And Export Again")
    else:
        message_bit = "Export Successful!"
    self.message_user(request, "%s" % message_bit)
    
export_results.short_description = 'Export Result'