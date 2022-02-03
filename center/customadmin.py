from __future__ import unicode_literals
from django.contrib import admin
from django.conf.urls import url
from django.contrib.admin import helpers
from django.db.models import When, F, Q
from django.conf import settings
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.mail.message import EmailMessage
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from mngr.views import rannum, ranlet, send_sms, send_bbn_sms
from .models import (CenterCode, CenterUserScript, CenterUserBank, CenterResult, 
    CenterSendResult, CenterSubjectScore, Candidate)
from bank.models import Question
from .forms import CodesForm, SalesForm, UserImportForm, DeactivateForm, UserDataForm
import csv, StringIO #io
import os
from django.utils import timezone
import datetime
from datetime import timedelta
from decimal import Decimal

User = get_user_model()


def get_users(modeladmin, request, queryset):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Users.csv"'#"somefilename.csv"'
    writer = csv.writer(response)
    buyer = ''
    qty = 0
    message_bit = None
    for card in queryset:
        if card.issued:
            if buyer != '':
                if not card.buyer == buyer:
                    message_bit = " These users are not for the same center!"
            else:
                buyer = card.buyer
            new_user = User.objects.get(username=card.user)
            qty += 1
            writer.writerow([card.pin,card.srn,new_user.username,new_user.id,
                new_user.date_joined,card.buyer,card.set_name])   
        else:
            message_bit = " You Can Only Export Issued Codes!" 
    if message_bit:
        modeladmin.message_user(request, "%s" % message_bit, level=messages.ERROR)
    else:
        return response
                    
get_users.short_description = 'Export Users For Selected Codes'


def deissue_code(modeladmin, request, queryset):
    for card in queryset:
        if card.issued:
            if not card.used:
                card.issued = False
                card.active = False
                card.buyer = ''
                card.set_name = ''
                card.save()
                message_bit = str(card.srn) + " Successfully De-issued!"
                modeladmin.message_user(request, "%s" % message_bit)
                    
deissue_code.short_description = 'De-issue Selected Codes'


class CenterCodeAdmin(admin.ModelAdmin):
    list_display = ('pin', 'srn', 'user', 'buyer', 'active', 'used',)
    search_fields = ('pin', 'srn', 'user')
    list_filter = ('issued', 'active', 'generated', 'buyer', 'set_name', 'used')
    actions = [get_users, deissue_code, 'print_reg_num']

    # actions = ['activate_card', 'deactivate_card']


    def get_urls(self):
        urls = super(CenterCodeAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^codes/$',
                self.admin_site.admin_view(self.codes),
                name='center_centercode_codes',
            ),
            url(
                r'^sales/$',
                self.admin_site.admin_view(self.sales),
                name='center_centercode_sales',
            ),
        ]
        return custom_urls + urls

    def print_reg_num(self, request, queryset):
        buyer = ''
        set_name = ''
        message_bit = None
        for card in queryset:
            if card.issued:
                if card.used:
                    message_bit = " Remove Used Codes!"
                else:
                    if buyer == '':
                        buyer = card.buyer
                        set_name = card.set_name
                    else:
                        if not card.buyer == buyer:
                            message_bit = " These users are not for the same center!"
                        else:
                            if not card.set_name == set_name:
                                message_bit = " These users are not of the same set!"
            else:
                message_bit = " Some Of These Cards Have Not Been Issued To Any Center!"
        if message_bit:
            self.message_user(request, "%s" % message_bit, level=messages.ERROR)
        else:
            context_instance={'regnum':queryset,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
            'buyer':buyer,
            'set_name':set_name}
            return render(request,
                            'admin/center/centercode/print_regnum.html',
                            context_instance)
    print_reg_num.short_description = 'Print Registration Numbers'

    def codes(self, request):
        code_list = []
        context = {
            'title': 'GET CODES',
            'code_list' : code_list,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = CodesForm(request.POST)
            if form.is_valid():
                number = form.cleaned_data['number']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    qty = 0
                    while qty < int(number):
                        pn = rannum(6)
                        #fetch last centercode
                        accesses = CenterCode.objects.all().order_by('srn')
                        counted = len(accesses)
                        if counted == 0:
                            serial = 'CC10001'
                        else:
                            last = accesses[(counted-1)]
                            #the corresponding serial stripped of letters and incremented
                            lastsrn = str(last.srn)
                            onlynum = lastsrn[2:7]
                            lastnum = int(onlynum)
                            newnum = lastnum + 1
                            #recreate
                            serial = 'CC' + (str(newnum))

                        newcode = CenterCode(
                        pin = pn,
                        srn = serial)
                        newcode.save()

                        code_list.append(newcode)
                        qty += 1
                    mesgbody = 'You generated '+ str(qty) + ' center codes.'
                    smesto = '2348027721770'
                    try:
                        send_bbn_sms(mesgbody, smesto)
                    except Exception:
                        pass
                    form = CodesForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/center/centercode/codes.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
        else:
            form = CodesForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/center/centercode/codes.html', context)


    def sales(self, request):
        qty = 0
        used = 0
        nil = []
        context = {
            'title': 'ISSUE CODES',
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
                set_name = form.cleaned_data['set_name']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    first = start[2:7]
                    prefix = start[0:2]
                    cardnum = int(first)
                    last = finish[2:7]
                    lastnum = int(last) + 1

                    email = EmailMessage(str(buyer)+' '+str(set_name)+' Users', ' ', 'noreply@mockexamsng.com',
                        ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

                    #attach users
                    attachment_csv_file = StringIO.StringIO()
                    writer = csv.writer(attachment_csv_file)
                    while cardnum < lastnum:
                        dg = rannum(8)
                        lt = ranlet(2)
                        regnum = str(dg) + lt
                        serial = str(prefix) + (str(cardnum))
                        if not CenterCode.objects.filter(srn=serial).exists():
                            cardnum += 1
                            nil.append(serial)
                        else:
                            card = CenterCode.objects.get(srn=serial)
                            if card.used:
                                used += 1
                                cardnum += 1
                            else:
                                if card.user:
                                    card.buyer = buyer
                                    card.set_name = set_name
                                    card.issued = True
                                    card.active = True
                                    # card.time_used = timezone.localtime(timezone.now())
                                    card.save()
                                    new_user = User.objects.get(username=card.user)
                                    cardnum += 1
                                    qty += 1
                                    writer.writerow([card.pin,card.srn,new_user.username,new_user.id,
                                        new_user.date_joined,card.buyer,card.set_name])
                                else:
                                    card.buyer = buyer
                                    card.set_name = set_name
                                    card.issued = True
                                    card.active = True
                                    card.user = regnum
                                    # card.time_used = timezone.localtime(timezone.now())
                                    card.save()
                                    new_user = User.objects.create_user(username=regnum, password=card.pin)
                                    cardnum += 1
                                    qty += 1
                                    writer.writerow([card.pin,card.srn,new_user.username,new_user.id,
                                        new_user.date_joined,card.buyer,card.set_name])
                    email.attach('attached_users.csv', attachment_csv_file.getvalue(),
                        'text/csv')
                    if qty < 1:
                        context['messaged'] = 'Email not sent, check quantity issued'
                    else:
                        try:
                            email.send(fail_silently=False)
                        except Exception:
                            context['messaged'] = 'Email not sent, check internet connection'
                    context['buyer'] = buyer
                    context['set_name'] = set_name
                    context['qty'] = qty
                    context['nil'] = nil
                    form = SalesForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/center/centercode/sales.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
        else:
            form = SalesForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/center/centercode/sales.html', context)



def take_offline(modeladmin, request, queryset):
    for pers in queryset:
        pers.online = False
        pers.save()
        message_bit = str(pers.user.username)+" Successfully Taken Offline!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
take_offline.short_description = 'Take Candidate(s) Offline'

def reset_questions(modeladmin, request, queryset):
    for pers in queryset:
        exam = pers.examination
        subjects = pers.subject.all()
        userques = CenterUserScript.objects.filter(user = pers)
        #clear the userscripts
        for i in userques:
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
                                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name),
                                     topic=str(tp), subtopic=str(i)).order_by('?','group_name')[:(int(i.to_do))]
                                bulk_script = []
                                for ques in que_set:
                                    new_script = CenterUserScript()
                                    new_script.question = ques
                                    new_script.user = pers
                                    bulk_script.append(new_script)
                                CenterUserScript.objects.bulk_create(bulk_script)
                                subtpunit += 1
                            else:
                                pass
                    else:
                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name),
                             topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                        bulk_script = []
                        for ques in que_set:
                            new_script = CenterUserScript()
                            new_script.question = ques
                            new_script.user = pers
                            bulk_script.append(new_script)
                        CenterUserScript.objects.bulk_create(bulk_script)
                            
            else:
                que_set = Question.objects.filter(examination=str(exam), 
                    subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                bulk_script = []
                for ques in que_set:
                    new_script = CenterUserScript()
                    new_script.question = ques
                    new_script.user = pers
                    bulk_script.append(new_script)
                CenterUserScript.objects.bulk_create(bulk_script)
        message_bit = str(pers.user.username)+" Questions Successfully Reset!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
reset_questions.short_description = 'Reset Candidate(s) Questions'


class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'subss', 'user', 'exam_center', 'taken_test')
    list_filter = ('online', 'issued_by', 'sex', 'regdate', 'exam_center')
    fields = ('user', 'full_name', 'phone', 'subject', 'online')
    readonly_fields = ('user',)
    search_fields = ('full_name', 'user__username')
    actions = [take_offline, reset_questions, 'export_results', 'sendresults']


    def get_actions(self, request):
        actions = super(CandidateAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
            if 'sendresults' in actions:
                del actions['sendresults']
        return actions


    def get_urls(self):
        urls = super(CandidateAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^addusers/$',
                self.admin_site.admin_view(self.addusers),
                name='center_candidate_addusers',
            ),
            url(
                r'^candidatedata/$',
                self.admin_site.admin_view(self.candidatedata),
                name='center_candidate_candidatedata',
            ),
            url(
                r'^deactivatelost/$',
                self.admin_site.admin_view(self.deactivatelost),
                name='center_candidate_deactivatelost',
            ),
        ]
        return custom_urls + urls

    def deactivatelost(self, request):
        context = {
            'title': 'DEACTIVATE LOST CODES',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = DeactivateForm(request.POST)
            if form.is_valid():
                regnum = form.cleaned_data['regnum']
                set_name = form.cleaned_data['set_name']
                buyer = form.cleaned_data['buyer']
                if regnum:
                    card = CenterCode.objects.get(user=regnum)
                    card.alert = True
                    card.alert_by = request.user
                    card.save()
                if set_name and buyer:
                    for card in CenterCode.objects.filter(buyer=buyer, set_name=set_name):
                        card.alert = True
                        card.alert_by = request.user
                        card.save()
                context['success'] = True
                context['buyer'] = buyer
                context['set_name'] = set_name
                context['regnum'] = regnum
                form = DeactivateForm()
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                            self.get_prepopulated_fields(request))
                return render(request, 'admin/center/candidate/deactivate_lost.html', context)
            else:
                message_bit = "INVALID DATA!"
                self.message_user(request, "%s" % message_bit)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                            self.get_prepopulated_fields(request))
                return render(request, 'admin/center/candidate/deactivate_lost.html', context)
        else:
            form = SalesForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                            self.get_prepopulated_fields(request))
            return render(request, 'admin/center/candidate/deactivate_lost.html', context)


    def addusers(self, request):
        code_list = []
        context = {
            'title': 'IMPORT USERS',
            'code_list' : code_list,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = UserImportForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                name = form.cleaned_data['file_name']
                dfile = CenterUserBank.objects.get(file_name=name)
                parturl = dfile.user_file
                fileurl = os.path.join(settings.MEDIA_ROOT, str(parturl))
                with open(str(fileurl)) as f:
                    reader = csv.reader(f)
                    for row in reader:
                        try:
                            code = CenterCode.objects.get(pin=row[0], srn=row[1])
                            try:
                                User.objects.get(username=row[2])
                                message_bit = "USER ALREADY UPLOADED!"
                            except User.DoesNotExist:
                                if not code.issued:
                                    User.objects.create_user(id=row[3], username=row[2], password=row[0], 
                                        date_joined=row[4])
                                    code.issued = True
                                    code.user = row[2]
                                    code.buyer = row[5]
                                    code.set_name = row[6]
                                    code.active = True
                                    code.save()
                                    message_bit = "UPLOAD SUCCESSFUL!"
                                else:
                                    message_bit = "ISSUE ERROR!"
                        except CenterCode.DoesNotExist:
                            message_bit = "UPLOAD ERROR!"
                                                
                        self.message_user(request, "%s" % message_bit)
                    form = UserImportForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/center/candidate/add_users.html', context)
            else:
                message_bit = "INVALID UPLOAD!"
                self.message_user(request, "%s" % message_bit)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/center/candidate/add_users.html', context)
        else:
            form = UserImportForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/center/candidate/add_users.html', context)

    def candidatedata(self, request):
        code_list = []
        context = {
            'title': 'IMPORT CANDIDATE DATA',
            'code_list' : code_list,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = UserDataForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                name = form.cleaned_data['file_name']
                dfile = CenterUserBank.objects.get(file_name=name)
                parturl = dfile.user_file
                fileurl = os.path.join(settings.MEDIA_ROOT, str(parturl))
                with open(str(fileurl)) as f:
                    reader = csv.reader(f)
                    for row in reader:
                        try:
                            code = CenterCode.objects.get(pin=row[0], srn=row[1])
                            try:
                                User.objects.get(username=row[2])
                                message_bit = "USER ALREADY UPLOADED!"
                            except User.DoesNotExist:
                                if not code.issued:
                                    User.objects.create_user(id=row[3], username=row[2], password=row[0], 
                                        date_joined=row[4])
                                    code.issued = True
                                    code.user = row[2]
                                    code.buyer = row[5]
                                    code.set_name = row[6]
                                    code.save()
                                    message_bit = "UPLOAD SUCCESSFUL!"
                                else:
                                    message_bit = "ISSUE ERROR!"
                        except CenterCode.DoesNotExist:
                            message_bit = "UPLOAD ERROR!"
                                                
                        self.message_user(request, "%s" % message_bit)
                    form = UserDataForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/center/candidate/candidatedata.html', context)
            else:
                message_bit = "INVALID UPLOAD!"
                self.message_user(request, "%s" % message_bit)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/center/candidate/candidatedata.html', context)
        else:
            form = UserDataForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/center/candidate/candidatedata.html', context)


    def export_results(self, request, queryset):
        email = EmailMessage(str(request.user) + ' Center Result', ' ', 'mockexamsng@gmail.com',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])
        
        #attach results
        attachment_csv_file1 = StringIO.StringIO()
        writer1 = csv.writer(attachment_csv_file1)
        #attach subject scores
        attachment_csv_file2 = StringIO.StringIO()
        writer2 = csv.writer(attachment_csv_file2)
        #attach candidate
        attachment_csv_file3 = StringIO.StringIO()
        writer3 = csv.writer(attachment_csv_file3)
        #insert header
        writer1.writerow(['id', 'timestamp', 'started', 'time_started', 'time_ended', 'done',
                'marked', 'total','duration', 'exam_center_id', 'user_id'])
        writer2.writerow(['id', 'subject', 'score', 'user_id'])
        writer3.writerow(['id', 'code_used', 'time_used', 'user_id', 'full_name', 
            'sex', 'phone', 'exam_center', 'issued_by', 'examination', 
            'subjects', 'regdate'])
    
        for user in queryset:
            result = CenterResult.objects.get(user=user)
            if not result.marked:
                result.save()
            candidate = Candidate.objects.get(user__username=user.user.username)
            subject = ""
            for j in candidate.subject.all():
                subject += (str(j.id)) + ','
            code_used = CenterCode.objects.get(srn=candidate.regnum, user=candidate.user.username)
            writer3.writerow([candidate.id, candidate.regnum, code_used.time_used, 
                candidate.user_id, candidate.full_name, candidate.sex, candidate.phone, 
                candidate.exam_center_id, candidate.issued_by, candidate.examination_id, 
                subject, candidate.regdate])
            #result = CenterResult.objects.get(user=user)
            writer1.writerow([result.id, result.timestamp, int(result.started), result.time_started, 
                result.time_ended, int(result.done), int(result.marked), result.total, result.duration, 
                result.exam_center.id, result.user.id])
            for score in CenterSubjectScore.objects.filter(user=user.regnum):
                writer2.writerow([score.id, score.subject, score.score, score.user])

        email.attach('attachment_result.csv', attachment_csv_file1.getvalue(),
            'text/csv')
        email.attach('attachment_score.csv', attachment_csv_file2.getvalue(),
            'text/csv')
        email.attach('attachment_users.csv', attachment_csv_file3.getvalue(),
            'text/csv')            
        try:
            email.send(fail_silently=False)
        except Exception:
            message_bit = ("Export Not Successful, Check Internet And Export Again")
        else:
            message_bit = "Export Successful!"
        self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export Result'


    def sendresults(self, request, queryset):
        for pers in queryset:
            try:
                result = CenterResult.objects.get(user=pers)
            except CenterResult.DoesNotExist:
                pass
            else:
                if result.marked:
                    try:
                        dphone = int(result.user.phone)
                        smsto = '234'+str(dphone)
                        t = str(result.user.full_name[:20])+" MOCK RESULT:"
                        for r in result.scores:
                            t = t+str(r)+" "
                        mesgbody =  t 
                        smesto = str(smsto)
                        usersend = CenterSendResult.objects.filter(user = str(result.user))
                        if usersend.exists():
                            message_bit = str(result.user) + " result previously sent!"
                        else:
                            try:
                                send_bbn_sms(mesgbody, smesto)
                            except Exception:
                                message_bit = (" Result Sending Not Successful for Number "+str(pers.user)+
                                ". Check Internet and Send Again")
                            else:
                                message_bit = "Result Sending Successful for Number "+str(pers.user)+"!"
                                sendnew = CenterSendResult(
                                user = str(result.user),
                                result= result)
                                sendnew.save()
                    except Exception:
                        message_bit = (" Result Sending Not Successful for Number "+str(pers.user)+
                                ". Check Phone Number and Send Again")
                    self.message_user(request, "%s" % message_bit)
                        

    sendresults.short_description = 'Send Selected User Result'



class CenterSubjectScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'score', 'remarking')
    fields = ('user', 'subject', 'score')
    read_only_fields = ('user', 'subject', 'score')

    def get_actions(self, request):
        actions = super(CenterSubjectScoreAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions



class CenterResultAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'exam_center', 'time_started', 'total', 'done', 'marked')
    fields = ('user', 'done', 'marked', 'duration', 'scripts')
    read_only_fields = ('user', )
    search_fields = ('user__full_name', 'user__user__username', 'user__regnum')
    list_filter = ('exam_center', 'time_started', 'done', 'marked')
    actions = ['reset_time', 'print_results', 'mark_scripts', 'remark_scripts']

    def get_actions(self, request):
        actions = super(CenterResultAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def mark_scripts(self, request, queryset):
        for pers in queryset:
            if not pers.marked:
                pers.markscript()
                if pers.marked:
                    message_bit = str(pers.user.regnum)+" Scripts Successfully Marked!"
                    self.message_user(request, "%s" % message_bit)
                        
    mark_scripts.short_description = 'Mark Candidate(s) Scripts'

    def remark_scripts(self, request, queryset):
        for pers in queryset:
            pers.marked = False
            pers.save()
            pers.markscript()
            if pers.marked:
                message_bit = str(pers.user.regnum)+" Scripts Successfully Remarked!"
                self.message_user(request, "%s" % message_bit)
                        
    remark_scripts.short_description = 'Remark Candidate(s) Scripts'

    # def get_urls(self):
    #     urls = super(CenterResultAdmin, self).get_urls()
    #     custom_urls = [
    #         url(
    #             r'^export_results/$',
    #             self.admin_site.admin_view(self.export_results),
    #             name='center_centerresult_export_results',
    #         ),
    #         url(
    #             r'^sendresults/$',
    #             self.admin_site.admin_view(self.sendresults),
    #             name='center_centerresult_sendresults',
    #         ),
    #     ]
    #     return custom_urls + urls

    # def export_results(self, request, queryset):

    #     import csv, StringIO #StringIO
    #     for btch in queryset:
    #         email = EmailMessage(str(btch.center)+'(Batch'+str(btch.period)+')' +'Result', ' ', ' ',
    #             ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

    #         #attach results
    #         attachment_csv_file = StringIO.StringIO()

    #         writer = csv.writer(attachment_csv_file)

    #         writer.writerow(['time_started', 'time_ended', 'done', 'marked', 'total','batch', 
    #             'exam_center', 'user'])
    #         reslt = CenterResult.objects.filter(batch=btch)
    #         users = reslt.values_list('time_started', 'time_ended', 'done', 'marked', 'total','batch', 
    #             'exam_center', 'user')
    #         for i in users:
    #             # pers = i.user.user
    #             # profl = CenterResult.objects.get(user=pers)
    #             # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, 
    #             #profl.marked, profl.total,)
    #             writer.writerow(i)

    #         email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
    #         'text/csv')

    #         #attach subject scores
    #         attachment_csv_file = StringIO.StringIO()

    #         writer = csv.writer(attachment_csv_file)

    #         writer.writerow(['subject', 'score', 'user'])
    #         profiles = Candidate.objects.filter(batch=btch)
    #         for pf in profiles:
    #             uscores = CenterSubjectScore.objects.filter(user=str(pf.user))
    #             scores = uscores.values_list('subject', 'score', 'user')
    #             for i in scores:
    #                 writer.writerow(i)

    #         email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
    #         'text/csv')

    #         # #attach special cases
    #         # attachment_csv_file = StringIO.StringIO()

    #         # writer = csv.writer(attachment_csv_file)

    #         # writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
    #         # profiles = Candidate.objects.filter(batch=btch)
    #         # for pf in profiles:
    #         #     script = CenterUserScript.objects.filter(regnumber=str(pf.regnum))
    #         #     scripts = case.values_list('regnumber', 'issue', 'message', 'noresult')
    #         #     for i in cases:
    #         #         writer.writerow(i)

    #         # email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
    #         # 'text/csv')
    #         try:
    #             email.send(fail_silently=False)
    #         except Exception:
    #             message_bit = ("Export Not Successful for "+str(btch.center)+" Batch("+str(btch.period)
    #                 +"). Check Internet and Export Again")
    #         else:
    #             message_bit = "Export Successful for "+str(btch.center)+" Batch("+str(btch.period)+"!"
    #         self.message_user(request, "%s" % message_bit)
        
    # export_results.short_description = 'Export Result'


    # #@permission_required('batch.send')
    # def sendresults(self, request, queryset):
    #     for btch in queryset:
    #         users = Candidate.objects.filter(batch=btch)
    #         for pers in users:
    #             try:
    #                 result = CenterResult.objects.get(user=pers)
    #             except CenterResult.DoesNotExist:
    #                 pass
    #             else:
    #                 if result.marked:
    #                     try:
    #                         dphone = int(result.user.phone)
    #                         smsto = '234'+str(dphone)
    #                         t = str(result.user.full_name[:20])+" MOCK RESULT:"
    #                         for r in result.scores:
    #                             t = t+str(r)+" "
    #                         mesgbody =  t 
    #                         smesto = str(smsto)
    #                         usersend = CenterSendResult.objects.filter(user = str(result.user))
    #                         if usersend.exists():
    #                             message_bit = str(result.user) + " result previously sent!"
    #                         else:
    #                             try:
    #                                 send_bbn_sms(mesgbody, smesto)
    #                             except Exception:
    #                                 message_bit = (" Result Sending Not Successful for Number "+str(pers.user)+
    #                                 ". Check Internet and Send Again")
    #                             else:
    #                                 message_bit = "Result Sending Successful for Number "+str(pers.user)+"!"
    #                                 sendnew = CenterSendResult(
    #                                 user = str(result.user),
    #                                 result= result)
    #                                 sendnew.save()
    #                     except Exception as e:
    #                         message_bit = (" Result Sending Not Successful for Number "+str(pers.user)+
    #                                 ". Check Phone Number and Send Again")
    #                     self.message_user(request, "%s" % message_bit)
                        

    # sendresults.short_description = 'Send Center Result'

    # def markscripts(self, request, queryset):
    #     for script in queryset:
    #         if script.marked:
    #             message_bit = str(script.user)+" Script Already Marked!"
    #         else:
    #             try:
    #                 script.save()
    #                 if script.marked:
    #                     message_bit = str(script.user)+" Script Successfully Marked!"
    #                 else:
    #                     message_bit = str(script.user)+" Script Not Marked!"
    #             except Exception:
    #                 message_bit = str(script.user)+" Script Not Ready For Marking!"
    #         self.message_user(request, "%s" % message_bit)
                        
    # markscripts.short_description = 'Mark Selected Scripts'

    def reset_time(self, request, queryset):
        for pers in queryset:
            pers.duration = 0
            pers.done = False
            pers.marked = False
            pers.time_started = timezone.localtime(timezone.now())
            pers.save()
            message_bit = str(pers.user.regnum)+" Time Successfully Reset!"
            self.message_user(request, "%s" % message_bit)
                        
    reset_time.short_description = 'Reset Candidate(s) Time'

    def print_results(self, request, queryset):
        titled = queryset[0]
        profiles = []
        for i in queryset:
            if i.marked:
                profiles.append(i)
        context_instance={'profiles':profiles,
        'app_label': self.model._meta.app_label,
        'opts': self.model._meta,
        'has_change_permission': self.has_change_permission(request),
         'titled':titled}
        return render(request,
                          'admin/center/centerresult/results.html',
                          context_instance)
    print_results.short_description = 'Print Results'

