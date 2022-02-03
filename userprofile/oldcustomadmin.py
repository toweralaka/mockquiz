# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.mail.message import EmailMessage
from django.contrib.auth.decorators import permission_required
from django.contrib.admin import helpers
from django.shortcuts import render
from django.conf.urls import url

from django.contrib.auth.models import User
from .forms import WriteForm
from mngr.forms import SalesForm
from .models import (ExamCenter, UserProfile, Photocard, Batch, Result, SendResult, 
                        WriteAccess, ExamSession, SubjectScore, SpecialCase)
from bank.models import Topic, Examination, Subject, Question, SubTopic
from mngr.models import AccessCode
from mngr.views import send_sms
import requests
import csv


#define custom admin actions here

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
                smesto = str(result.user.phone)
                usersend = SendResult.objects.filter(user = str(result.user.regnum))
                if usersend.exists():
                    message_bit = str(result.user.regnum) + " Result Previously Sent!"
                else:
                    try:
                        send_sms(mesgbody, smesto)
                    except IndexError:
                        message_bit = "There Is No Result To Send"
                    except Exception as e:
                        message_bit = " Result Sending Not Successful for Number "+str(pers.regnum)+". Check Internet and Send Again"
                    else:
                        message_bit = "Result Sending Successful for Number "+str(pers.regnum)+"!"
                    modeladmin.message_user(request, "%s" % message_bit)
                    sendnew = SendResult(
                        user = str(result.user.regnum),
                        result= result)
                    sendnew.save()

senduserresult.short_description = 'Send User Result'




class BatchAdmin(admin.ModelAdmin):
    fields = ('exam_center', 'number', 'capacity', 'date', 'time', 'show_result', 'active', 'write_exam')
    #readonly_fields = ('exam_center', 'number', 'capacity', 'date', 'time', 'show_result', 'active')
    list_display = ('exam_center', 'number', 'capacity', 'qty', 'date', 'time', 'write_exam', 'show_result',)# 'batch_actions')
    search_fields = ('exam_center__name', )
    actions = ['activate_batch', 'sendresults', 'export_results', 'activate_client', show_results, hide_results]

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
                        allsess = ExamSession.objects.all()
                        allsess.delete()
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
                                                            que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                            bulk_exmsess = []
                                                            for ques in que_set:
                                                                new_sess = ExamSession()
                                                                new_sess.question = str(ques.id)
                                                                new_sess.user = up
                                                                bulk_exmsess.append(new_sess)
                                                            ExamSession.objects.bulk_create(bulk_exmsess)
                                                            subtpunit += 1
                                                        else:
                                                            pass
                                                else:
                                                    que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                    bulk_exmsess = []
                                                    for ques in que_set:
                                                        new_sess = ExamSession()
                                                        new_sess.question = str(ques.id)
                                                        new_sess.user = up
                                                        bulk_exmsess.append(new_sess)
                                                    ExamSession.objects.bulk_create(bulk_exmsess)



                                                # que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                # #the list that will hold the bulk insert
                                                # bulk_exmsess = []
                                                 
                                                # #loop that list and make those objects
                                                # for ques in que_set:
                                                #     new_sess = ExamSession()
                                                #     new_sess.question = str(ques.id)
                                                #     new_sess.user = up
                                                     
                                                #     #add game to the bulk list
                                                #     bulk_exmsess.append(new_sess)
                                                 
                                                # #now with a list of game objects that want to be created, run bulk_create on the chosen model
                                                # ExamSession.objects.bulk_create(bulk_exmsess)
                                                #     # sesques = ExamSession(
                                                #     # user = up,
                                                #     # question = str(ques.id))
                                                #     # sesques.save()
                                        else:
                                            que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                            bulk_exmsess = []
                                            for ques in que_set:
                                                new_sess = ExamSession()
                                                new_sess.question = str(ques.id)
                                                new_sess.user = up
                                                bulk_exmsess.append(new_sess)
                                            ExamSession.objects.bulk_create(bulk_exmsess)
                                                # sesques = ExamSession(
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
                                                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                                        bulk_exmsess = []
                                                        for ques in que_set:
                                                            new_sess = ExamSession()
                                                            new_sess.question = str(ques.id)
                                                            new_sess.user = up
                                                            bulk_exmsess.append(new_sess)
                                                        ExamSession.objects.bulk_create(bulk_exmsess)
                                                        subtpunit += 1
                                                    else:
                                                        pass
                                            else:
                                                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                                                bulk_exmsess = []
                                                for ques in que_set:
                                                    new_sess = ExamSession()
                                                    new_sess.question = str(ques.id)
                                                    new_sess.user = up
                                                    bulk_exmsess.append(new_sess)
                                                ExamSession.objects.bulk_create(bulk_exmsess)
                                    else:
                                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                                        bulk_exmsess = []
                                        for ques in que_set:
                                            new_sess = ExamSession()
                                            new_sess.question = str(ques.id)
                                            new_sess.user = up
                                            bulk_exmsess.append(new_sess)
                                        ExamSession.objects.bulk_create(bulk_exmsess)
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

        import csv, StringIO
        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user'])
            reslt = Result.objects.filter(batch=btch)
            users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
            for i in users:
                # pers = i.user.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, profl.marked, profl.total,)
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

            #attach special cases
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
                cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
                for i in cases:
                    writer.writerow(i)

            email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception as e:
                message_bit = "Export Not Successful for Batch Number "+str(btch.number)+". Check Internet and Export Again"
            else:
                message_bit = "Export Successful for Batch Number "+str(btch.number)+"!"
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
                                message_bit = " Result Sending Not Successful for Number "+str(pers.regnum)+". Check Internet and Send Again"
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
                            userp = UserProfile.objects.get(serial=i.srn)#, batch=btch)##btch may or may not be filtered
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




class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'subss', 'surname', 'buyer', 'phone', 'examination', 'exam_area', 'batch', 'image_tag','pc')
    readonly_fields = ('image_tag',)
    search_fields = ('regnum', 'surname', 'first_name', 'serial')
    list_filter = ('regdate', 'examination', 'exam_area', 'exam_center', 'batch')
    #fields = ('first_name', 'subject', 'online')
    actions = ['print_photo_album', 'deactivate_user', 'activate_user', senduserresult]

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
        ]
        return custom_urls + urls

    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'print_photo_album' in actions:
                del actions['print_photo_album']
            if 'senduserresult' in actions:
                del actions['senduserresult']
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

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